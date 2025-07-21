"""Base Event class for py-micro-plumberd."""

import uuid
from typing import Any, Dict


class Event:
    """Base class for all events.
    
    Automatically generates a unique ID (lowercase UUID with dashes) for each event instance.
    Events should be immutable after creation.
    """
    
    def __init__(self) -> None:
        """Initialize event with a unique ID."""
        self.id: str = str(uuid.uuid4()).lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization.
        
        Returns dict with PascalCase property names for C# compatibility.
        """
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                # Convert snake_case to PascalCase for C# compatibility
                pascal_key = self._to_pascal_case(key)
                result[pascal_key] = value
        return result
    
    @staticmethod
    def _to_pascal_case(snake_str: str) -> str:
        """Convert snake_case to PascalCase."""
        if snake_str == 'id':
            return 'Id'
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)