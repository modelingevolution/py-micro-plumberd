"""Stream name formatting for py-micro-plumberd."""


class StreamName:
    """Represents an EventStore stream name following the {Category}-{StreamId} convention."""

    def __init__(self, category: str, stream_id: str) -> None:
        """Initialize a stream name.

        Args:
            category: The stream category (e.g., "Recording", "User", "Order")
            stream_id: The unique stream identifier (typically a UUID)
        """
        if not category:
            msg = "Category cannot be empty"
            raise ValueError(msg)
        if not stream_id:
            msg = "Stream ID cannot be empty"
            raise ValueError(msg)

        self.category = category
        self.stream_id = stream_id

    def __str__(self) -> str:
        """Return the formatted stream name."""
        return f"{self.category}-{self.stream_id}"

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"StreamName(category='{self.category}', stream_id='{self.stream_id}')"

    @classmethod
    def parse(cls, stream_name: str) -> "StreamName":
        """Parse a stream name string into a StreamName object.

        Args:
            stream_name: The stream name in format {Category}-{StreamId}

        Returns:
            StreamName object

        Raises:
            ValueError: If the stream name format is invalid
        """
        parts = stream_name.split("-", 1)
        expected_parts = 2
        if len(parts) != expected_parts:
            msg = f"Invalid stream name format: {stream_name}"
            raise ValueError(msg)

        return cls(category=parts[0], stream_id=parts[1])
