"""Base Event class for py-micro-plumberd using Pydantic v2."""

from uuid import UUID, uuid4
from typing import Any, Dict

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from pydantic.alias_generators import to_pascal


class Event(BaseModel):
    """Base class for all events using Pydantic v2.

    Provides automatic PascalCase serialization for EventStore compatibility
    while maintaining Pythonic snake_case in code.

    Example:
        >>> class RecordingStarted(Event):
        ...     pipeline_id: str
        ...     recording_path: str
        ...
        >>> event = RecordingStarted(
        ...     pipeline_id="pipeline-1",
        ...     recording_path="/recordings/test.mp4"
        ... )
        >>> # Use snake_case in Python code
        >>> print(event.pipeline_id)
        >>> # Automatically serializes to PascalCase for EventStore
        >>> data = event.model_dump(by_alias=True)
        >>> print(data["PipelineId"])
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

    id: UUID = Field(default_factory=lambda: uuid4())

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Serialize UUID as lowercase string with dashes for EventStore compatibility."""
        return str(value).lower()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary with PascalCase keys for EventStore.

        This method maintains backward compatibility with the original API.
        """
        return self.model_dump(by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary with PascalCase keys.

        This method provides deserialization from EventStore data.
        """
        return cls.model_validate(data)
