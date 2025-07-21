"""Stream name formatting for py-micro-plumberd."""

from typing import Optional


class StreamName:
    """Represents an EventStore stream name following the {Category}-{StreamId} convention."""
    
    def __init__(self, category: str, stream_id: str) -> None:
        """Initialize a stream name.
        
        Args:
            category: The stream category (e.g., "Recording", "User", "Order")
            stream_id: The unique stream identifier (typically a UUID)
        """
        if not category:
            raise ValueError("Category cannot be empty")
        if not stream_id:
            raise ValueError("Stream ID cannot be empty")
        
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
        parts = stream_name.split('-', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid stream name format: {stream_name}")
        
        return cls(category=parts[0], stream_id=parts[1])