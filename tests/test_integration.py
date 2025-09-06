"""Integration tests for py-micro-plumberd with Pydantic v2."""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Optional

import pytest
from esdbclient import EventStoreDBClient

from py_micro_plumberd import Event, EventStoreClient, Metadata, StreamName


# Test events using Pydantic v2 style
class RecordingFinished(Event):
    """Recording finished event."""

    recording_id: str
    duration: float
    file_path: str


class TaskCreated(Event):
    """Task created event."""

    title: str
    description: str
    assigned_to: Optional[str] = None


class TaskCompleted(Event):
    """Task completed event."""

    completed_by: str
    completion_notes: Optional[str] = None


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
        event = RecordingFinished(
            recording_id="rec-123", duration=120.5, file_path="/recordings/rec-123.mp4"
        )

        # Check format: lowercase UUID with dashes
        id_str = str(event.id).lower()
        assert len(id_str) == 36
        assert id_str.count("-") == 4
        assert id_str == id_str.lower()
        assert all(c in "0123456789abcdef-" for c in id_str)

    def test_event_to_dict_pascal_case(self):
        """Test that event properties are converted to PascalCase."""
        event = RecordingFinished(
            recording_id="rec-123", duration=120.5, file_path="/recordings/rec-123.mp4"
        )
        data = event.model_dump(by_alias=True)

        # Check PascalCase conversion
        assert "Id" in data
        assert "RecordingId" in data
        assert "Duration" in data
        assert "FilePath" in data

        # Check values
        assert data["RecordingId"] == "rec-123"
        assert data["Duration"] == 120.5
        assert data["FilePath"] == "/recordings/rec-123.mp4"

        # ID should be lowercase string
        assert isinstance(data["Id"], str)
        assert data["Id"] == data["Id"].lower()

    def test_pythonic_field_access(self):
        """Test that we use snake_case in Python code."""
        event = TaskCreated(
            title="Implement feature",
            description="Add new feature X",
            assigned_to="developer@example.com",
        )

        # Pythonic snake_case access
        assert event.title == "Implement feature"
        assert event.description == "Add new feature X"
        assert event.assigned_to == "developer@example.com"

    def test_optional_fields(self):
        """Test events with optional fields."""
        # With optional field
        task1 = TaskCreated(
            title="Implement feature",
            description="Add new feature X",
            assigned_to="developer@example.com",
        )
        data1 = task1.model_dump(by_alias=True)
        assert data1["Title"] == "Implement feature"
        assert data1["AssignedTo"] == "developer@example.com"

        # Without optional field
        task2 = TaskCreated(title="Fix bug", description="Fix issue Y")
        data2 = task2.model_dump(by_alias=True)
        assert data2["Title"] == "Fix bug"
        assert data2.get("AssignedTo") is None


class TestEventStoreIntegration:
    """Test EventStore integration."""

    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests require EventStore",
    )
    async def test_append_event(self, client, unique_stream):
        """Test appending an event to EventStore."""
        # Create event
        event = RecordingFinished(
            recording_id="rec-456", duration=180.0, file_path="/recordings/rec-456.mp4"
        )

        # Append to stream
        position = client.append_to_stream(stream=unique_stream, event=event)

        assert position is not None

        # Read back to verify
        stream_name = str(unique_stream)
        esdb_client = EventStoreDBClient(
            uri=os.getenv("EVENTSTORE_URL", "esdb://localhost:2113?tls=false")
        )

        try:
            events = list(esdb_client.read_stream(stream_name))
            assert len(events) == 1

            recorded_event = events[0]

            # Check event type
            assert recorded_event.type == "RecordingFinished"

            # Check data is PascalCase
            data = json.loads(recorded_event.data)
            assert "RecordingId" in data
            assert data["RecordingId"] == "rec-456"
            assert data["Duration"] == 180.0
            assert data["FilePath"] == "/recordings/rec-456.mp4"

            # Check metadata
            metadata_dict = json.loads(recorded_event.metadata)
            assert "$correlationId" in metadata_dict
            assert "$causationId" in metadata_dict
            assert metadata_dict["$causationId"] == str(event.id).lower()
        finally:
            esdb_client.close()

    @pytest.mark.skipif(
        os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
        reason="Integration tests require EventStore",
    )
    async def test_custom_metadata(self, client, unique_stream):
        """Test appending event with custom metadata."""
        # Create event with custom metadata
        event = TaskCompleted(
            completed_by="developer@example.com", completion_notes="All tests passing"
        )

        custom_metadata = Metadata(
            correlation_id="corr-123",
            additional_metadata={"user_id": "user-456", "session_id": "sess-789"},
        )

        # Append to stream
        position = client.append_to_stream(
            stream=unique_stream, event=event, metadata=custom_metadata
        )

        assert position is not None

        # Read back to verify metadata
        stream_name = str(unique_stream)
        esdb_client = EventStoreDBClient(
            uri=os.getenv("EVENTSTORE_URL", "esdb://localhost:2113?tls=false")
        )

        try:
            events = list(esdb_client.read_stream(stream_name))
            assert len(events) == 1

            recorded_event = events[0]
            metadata_dict = json.loads(recorded_event.metadata)

            # Check custom metadata
            assert metadata_dict["$correlationId"] == "corr-123"
            assert metadata_dict["user_id"] == "user-456"
            assert metadata_dict["session_id"] == "sess-789"
        finally:
            esdb_client.close()


class TestDeserialization:
    """Test deserialization from EventStore format."""

    def test_deserialize_from_pascal_case(self):
        """Test deserializing events from PascalCase (EventStore format)."""
        # Simulate data from EventStore
        pascal_data = {
            "Id": "12345678-1234-1234-1234-123456789012",
            "RecordingId": "rec-789",
            "Duration": 240.75,
            "FilePath": "/recordings/rec-789.mp4",
        }

        # Deserialize using Pydantic
        event = RecordingFinished.model_validate(pascal_data)

        # Access with snake_case
        assert event.recording_id == "rec-789"
        assert event.duration == 240.75
        assert event.file_path == "/recordings/rec-789.mp4"
        assert str(event.id).lower() == "12345678-1234-1234-1234-123456789012"

    def test_round_trip_serialization(self):
        """Test round-trip serialization."""
        original = TaskCreated(
            title="Test task", description="Test description", assigned_to="test@example.com"
        )

        # Serialize to PascalCase
        data = original.model_dump(by_alias=True)

        # Deserialize back
        restored = TaskCreated.model_validate(data)

        # Verify fields match
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.assigned_to == original.assigned_to
        assert str(restored.id).lower() == str(original.id).lower()
