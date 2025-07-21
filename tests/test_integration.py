"""Integration tests for py-micro-plumberd."""

import asyncio
import json
import os
import uuid
from datetime import datetime

import pytest
from esdbclient import EventStoreDBClient

from py_micro_plumberd import Event, EventStoreClient, Metadata, StreamName


# Test events matching C# examples
class RecordingFinished(Event):
    def __init__(self, recording_id: str, duration: float, file_path: str):
        super().__init__()
        self.recording_id = recording_id
        self.duration = duration
        self.file_path = file_path


class TaskCreated(Event):
    def __init__(self, title: str, description: str, assigned_to: str = None):
        super().__init__()
        self.title = title
        self.description = description
        self.assigned_to = assigned_to


class TaskCompleted(Event):
    def __init__(self, completed_by: str, completion_notes: str = None):
        super().__init__()
        self.completed_by = completed_by
        self.completion_notes = completion_notes


@pytest.fixture
def eventstore_url():
    """Get EventStore URL from environment or default."""
    return os.getenv("EVENTSTORE_URL", "esdb://localhost:2113?tls=false")


@pytest.fixture
def client(eventstore_url):
    """Create EventStore client."""
    client = EventStoreClient(eventstore_url)
    yield client
    client.close()


@pytest.fixture
def unique_stream():
    """Generate unique stream name for testing."""
    stream_id = str(uuid.uuid4())
    return StreamName(category="TestStream", stream_id=stream_id)


class TestEventFormat:
    """Test event format compatibility with C# micro-plumberd."""
    
    def test_event_id_format(self):
        """Test that event ID is lowercase UUID with dashes."""
        event = RecordingFinished("rec-123", 120.5, "/recordings/rec-123.mp4")
        
        # Check format: lowercase UUID with dashes
        assert len(event.id) == 36
        assert event.id.count('-') == 4
        assert event.id == event.id.lower()
        assert all(c in '0123456789abcdef-' for c in event.id)
    
    def test_event_to_dict_pascal_case(self):
        """Test that event properties are converted to PascalCase."""
        event = RecordingFinished("rec-123", 120.5, "/recordings/rec-123.mp4")
        data = event.to_dict()
        
        # Check PascalCase conversion
        assert "Id" in data
        assert "RecordingId" in data
        assert "Duration" in data
        assert "FilePath" in data
        
        # Check values
        assert data["Id"] == event.id
        assert data["RecordingId"] == "rec-123"
        assert data["Duration"] == 120.5
        assert data["FilePath"] == "/recordings/rec-123.mp4"
    
    


class TestEventStoreIntegration:
    """Test EventStore integration."""
    
    def test_append_single_event(self, client, unique_stream):
        """Test appending a single event."""
        event = RecordingFinished("rec-123", 120.5, "/recordings/rec-123.mp4")
        
        position = client.append_to_stream(unique_stream, event)
        assert position >= 0
    
    def test_append_multiple_events(self, client, unique_stream):
        """Test appending multiple events to same stream."""
        # Create task
        created = TaskCreated(
            title="Implement py-micro-plumberd",
            description="Create Python version",
            assigned_to="developer@example.com"
        )
        position1 = client.append_to_stream(unique_stream, created)
        
        # Complete task
        completed = TaskCompleted(
            completed_by="developer@example.com",
            completion_notes="Successfully implemented"
        )
        position2 = client.append_to_stream(unique_stream, completed)
        
        assert position2 > position1
    
    def test_event_readable_by_esdb_client(self, client, unique_stream, eventstore_url):
        """Test that events can be read using standard EventStore client."""
        # Write event using py-micro-plumberd
        event = RecordingFinished("rec-123", 120.5, "/recordings/rec-123.mp4")
        metadata = Metadata(test_id="integration-test")
        
        client.append_to_stream(unique_stream, event, metadata)
        
        # Read using raw EventStore client
        raw_client = EventStoreDBClient(uri=eventstore_url)
        try:
            events = list(raw_client.read_stream(str(unique_stream)))
            assert len(events) == 1
            
            recorded_event = events[0]
            
            # Check event type
            assert recorded_event.type == "RecordingFinished"
            
            # Check data format
            data = json.loads(recorded_event.data)
            assert data["Id"] == event.id
            assert data["RecordingId"] == "rec-123"
            assert data["Duration"] == 120.5
            assert data["FilePath"] == "/recordings/rec-123.mp4"
            
            # Check metadata format
            metadata_dict = json.loads(recorded_event.metadata)
            assert "Created" in metadata_dict
            assert "ClientHostName" in metadata_dict
            
        finally:
            raw_client.close()
    
    def test_stream_name_format(self, client, eventstore_url):
        """Test stream name formatting."""
        stream_id = str(uuid.uuid4())
        stream = StreamName(category="Recording", stream_id=stream_id)
        
        event = RecordingFinished("rec-123", 120.5, "/recordings/rec-123.mp4")
        client.append_to_stream(stream, event)
        
        # Verify stream name format
        expected_stream_name = f"Recording-{stream_id}"
        assert str(stream) == expected_stream_name
        
        # Verify event can be read with formatted name
        raw_client = EventStoreDBClient(uri=eventstore_url)
        try:
            events = list(raw_client.read_stream(expected_stream_name))
            assert len(events) == 1
        finally:
            raw_client.close()


class TestStreamName:
    """Test StreamName class."""
    
    def test_stream_name_formatting(self):
        """Test stream name formatting."""
        stream = StreamName(category="Recording", stream_id="12345")
        assert str(stream) == "Recording-12345"
    
    def test_stream_name_parsing(self):
        """Test parsing stream name."""
        stream = StreamName.parse("Recording-12345")
        assert stream.category == "Recording"
        assert stream.stream_id == "12345"
    
    def test_stream_name_with_uuid(self):
        """Test stream name with UUID."""
        uuid_str = "b27f9322-7d73-4d98-a605-a731a2c373c6"
        stream = StreamName(category="Task", stream_id=uuid_str)
        assert str(stream) == f"Task-{uuid_str}"
    
    def test_invalid_stream_name(self):
        """Test invalid stream name raises error."""
        with pytest.raises(ValueError):
            StreamName(category="", stream_id="123")
        
        with pytest.raises(ValueError):
            StreamName(category="Test", stream_id="")
        
        with pytest.raises(ValueError):
            StreamName.parse("InvalidFormat")