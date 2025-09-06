"""CommandBus implementation for micro-plumberd compatibility."""

import socket
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from esdbclient import EventStoreDBClient

from .event import Event


class CommandBus:
    """
    Python CommandBus compatible with C# micro-plumberd.
    Supports fire-and-forget commands only.
    """
    
    def __init__(self, client: EventStoreDBClient):
        """
        Initialize CommandBus with EventStore client.
        
        Args:
            client: EventStore client for writing commands
        """
        self.client = client
        self.session_id = str(uuid4())  # CommandBus's own session ID
        self.stream_in = f">SessionIn-{self.session_id}"
        self.stream_out = f">SessionOut-{self.session_id}"
        
    async def send_async(
        self,
        recipient_id: Union[str, UUID],
        command: Union[Event, Any],
        fire_and_forget: bool = True,
        timeout: Optional[float] = None
    ) -> None:
        """
        Send command through CommandBus infrastructure.
        
        Args:
            recipient_id: Target ID where command should be routed (e.g., UI's SessionId)
            command: Command to send (must be Pydantic model with 'id' field)
            fire_and_forget: If True, don't wait for response (default: True)
            timeout: Optional timeout in seconds (not used for fire-and-forget)
            
        Raises:
            NotImplementedError: If fire_and_forget is False (not supported)
        """
        if not fire_and_forget:
            raise NotImplementedError("Synchronous commands (fire_and_forget=False) not supported")
        
        # Get command ID (support both Event base class and any model with id field)
        if hasattr(command, 'id'):
            command_id = str(command.id)
        else:
            command_id = str(uuid4())
        
        # Build metadata exactly as C# CommandBus does
        metadata = {
            "$correlationId": command_id,
            "$causationId": command_id,
            "SessionId": self.session_id,  # CommandBus session
            "RecipientId": str(recipient_id),  # Where to route
            "Created": datetime.now(timezone.utc).isoformat(),
            "ClientHostName": socket.gethostname()
        }
        
        # Serialize command with PascalCase for EventStore
        if hasattr(command, 'model_dump'):
            # Pydantic v2 model
            event_data = command.model_dump(by_alias=True, mode='json')
        elif hasattr(command, 'dict'):
            # Pydantic v1 model (fallback)
            event_data = command.dict(by_alias=True)
        else:
            # Plain dict or other object
            event_data = command if isinstance(command, dict) else {"data": str(command)}
        
        # Get event type name
        event_type = command.__class__.__name__ if hasattr(command, '__class__') else 'Command'
        
        # Create EventStore event
        import json
        from esdbclient import NewEvent
        
        new_event = NewEvent(
            type=event_type,
            data=json.dumps(event_data).encode("utf-8"),
            metadata=json.dumps(metadata).encode("utf-8"),
            content_type="application/json",
        )
        
        # Write to CommandBus input stream
        # C# handlers will read this and route based on RecipientId
        self.client.append_to_stream(
            stream_name=self.stream_in,
            events=[new_event],
            current_version='any'
        )
    
    async def queue_async(
        self,
        recipient_id: Union[str, UUID],
        command: Union[Event, Any],
        fire_and_forget: bool = True,
        timeout: Optional[float] = None
    ) -> None:
        """
        Queue command for async processing.
        
        For simplicity, delegates to send_async.
        In C# this uses a pool for better throughput.
        
        Args:
            recipient_id: Target ID where command should be routed
            command: Command to queue
            fire_and_forget: If True, don't wait for response
            timeout: Optional timeout in seconds
        """
        await self.send_async(recipient_id, command, fire_and_forget, timeout)
    
    def close(self) -> None:
        """Close the CommandBus."""
        if hasattr(self.client, 'close'):
            self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
    
    def __enter__(self):
        """Sync context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self.close()