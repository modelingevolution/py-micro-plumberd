"""Test Pydantic v2 event implementation."""

import json
from typing import Optional

from py_micro_plumberd.event import Event


# Test events using Pydantic style
class RecordingFinished(Event):
    """Recording finished event using Pydantic."""

    recording_id: str
    duration: float
    file_path: str


class TaskCreated(Event):
    """Task created event using Pydantic."""

    title: str
    description: str
    assigned_to: Optional[str] = None


class TaskCompleted(Event):
    """Task completed event using Pydantic."""

    completed_by: str
    completion_notes: Optional[str] = None


class TestPydanticEventFormat:
    """Test Pydantic event format compatibility with C# micro-plumberd."""

    def test_event_id_format(self) -> None:
        """Test that event ID is lowercase UUID with dashes."""
        event = RecordingFinished(
            recording_id="rec-123",
            duration=120.5,
            file_path="/recordings/rec-123.mp4",
        )

        # Check format: lowercase UUID with dashes
        id_str = str(event.id).lower()
        uuid_length = 36
        uuid_dash_count = 4
        assert len(id_str) == uuid_length
        assert id_str.count("-") == uuid_dash_count
        assert id_str == id_str.lower()
        assert all(c in "0123456789abcdef-" for c in id_str)

    def test_pythonic_field_access(self) -> None:
        """Test that we can use snake_case in Python code."""
        event = RecordingFinished(
            recording_id="rec-123",
            duration=120.5,
            file_path="/recordings/rec-123.mp4",
        )

        # Pythonic snake_case access
        assert event.recording_id == "rec-123"
        expected_duration = 120.5
        assert event.duration == expected_duration
        assert event.file_path == "/recordings/rec-123.mp4"

    def test_event_to_dict_pascal_case(self) -> None:
        """Test that event properties are converted to PascalCase."""
        event = RecordingFinished(
            recording_id="rec-123",
            duration=120.5,
            file_path="/recordings/rec-123.mp4",
        )
        data = event.model_dump(by_alias=True)

        # Check PascalCase conversion
        assert "Id" in data
        assert "RecordingId" in data
        assert "Duration" in data
        assert "FilePath" in data

        # Check values
        assert data["RecordingId"] == "rec-123"
        expected_duration_data = 120.5
        assert data["Duration"] == expected_duration_data
        assert data["FilePath"] == "/recordings/rec-123.mp4"

        # ID should be lowercase string
        assert isinstance(data["Id"], str)
        assert data["Id"] == data["Id"].lower()

    def test_optional_fields(self) -> None:
        """Test events with optional fields."""
        # With optional field
        task1 = TaskCreated(
            title="Implement feature",
            description="Add new feature X",
            assigned_to="developer@example.com",
        )
        data1 = task1.model_dump(by_alias=True)
        assert data1["AssignedTo"] == "developer@example.com"

        # Without optional field
        task2 = TaskCreated(title="Fix bug", description="Fix issue Y")
        data2 = task2.model_dump(by_alias=True)
        assert data2.get("AssignedTo") is None

    def test_deserialization_from_pascal_case(self) -> None:
        """Test that we can deserialize from PascalCase (EventStore format)."""
        # Simulate data from EventStore
        pascal_data = {
            "Id": "12345678-1234-1234-1234-123456789012",
            "RecordingId": "rec-456",
            "Duration": 240.75,
            "FilePath": "/recordings/rec-456.mp4",
        }

        # Deserialize
        event = RecordingFinished.model_validate(pascal_data)

        # Access with snake_case
        assert event.recording_id == "rec-456"
        expected_duration = 240.75
        assert event.duration == expected_duration
        assert event.file_path == "/recordings/rec-456.mp4"
        assert str(event.id).lower() == "12345678-1234-1234-1234-123456789012"

    def test_json_serialization(self) -> None:
        """Test JSON serialization for EventStore."""
        event = TaskCompleted(
            completed_by="developer@example.com",
            completion_notes="All tests passing",
        )

        # Serialize to JSON
        data = event.model_dump(by_alias=True)
        json_str = json.dumps(data)

        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["CompletedBy"] == "developer@example.com"
        assert parsed["CompletionNotes"] == "All tests passing"
        assert "Id" in parsed

    def test_backward_compatibility_api(self) -> None:
        """Test that Pydantic serialization/deserialization works."""
        original = RecordingFinished(
            recording_id="rec-789",
            duration=360.0,
            file_path="/recordings/rec-789.mp4",
        )

        # Use backward compatible API
        data = original.model_dump(by_alias=True)
        restored = RecordingFinished.model_validate(data)

        # Verify round-trip
        assert restored.recording_id == original.recording_id
        assert restored.duration == original.duration
        assert restored.file_path == original.file_path
        assert str(restored.id).lower() == str(original.id).lower()

    def test_metadata_compatibility(self) -> None:
        """Test that events work with metadata."""
        event = TaskCreated(title="Test task", description="Test description")

        # Event should have an ID
        assert event.id is not None

        # to_dict should return PascalCase
        data = event.model_dump(by_alias=True)
        assert "Title" in data
        assert data["Title"] == "Test task"
