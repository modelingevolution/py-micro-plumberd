"""Base Event class for py-micro-plumberd using Pydantic v2."""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from pydantic.alias_generators import to_pascal


class Event(BaseModel):
    """Base class for all events using Pydantic v2.

    Automatically generates a unique ID (lowercase UUID with dashes) for each event instance.
    Events use snake_case in Python code but serialize to PascalCase for EventStore.

    Example:
        >>> from typing import Optional
        >>>
        >>> class RecordingFinished(Event):
        ...     recording_id: str
        ...     duration: float
        ...     file_path: str
        ...
        >>> event = RecordingFinished(
        ...     recording_id="rec-123",
        ...     duration=120.5,
        ...     file_path="/recordings/test.mp4"
        ... )
        >>>
        >>> # Use snake_case in Python code
        >>> print(event.recording_id)
        >>>
        >>> # Automatically serializes to PascalCase for EventStore
        >>> data = event.model_dump(by_alias=True)
        >>> print(data["RecordingId"])
    """

    model_config = ConfigDict(
        # Convert snake_case fields to PascalCase for serialization
        alias_generator=to_pascal,
        # Allow both snake_case and PascalCase when deserializing
        populate_by_name=True,
        # Use Enum values for serialization
        use_enum_values=True,
        # Extra fields are allowed for flexibility
        extra="allow",
    )

    id: UUID = Field(default_factory=uuid4)

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Serialize UUID as lowercase string with dashes for EventStore compatibility."""
        return str(value).lower()
