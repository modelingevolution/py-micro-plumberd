"""CommandBus implementation for micro-plumberd compatibility."""

import json
import socket
from datetime import datetime, timezone
from typing import Any, Optional, Union
from uuid import UUID, uuid4

from esdbclient import NewEvent, StreamState

from .client import EventStoreClient
from .event import Event


class CommandBus:
    """
    Python CommandBus compatible with C# micro-plumberd.
    Supports fire-and-forget commands only.
    """

    def __init__(self, client: EventStoreClient) -> None:
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
        command: Union[Event, Any],  # noqa: ANN401
        fire_and_forget: bool = True,
        timeout: Optional[float] = None,  # noqa: ARG002
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
            msg = "Synchronous commands (fire_and_forget=False) not supported"
            raise NotImplementedError(msg)

        # Get command ID (support both Event base class and any model with id field)
        command_id = str(command.id) if hasattr(command, "id") else str(uuid4())

        # Get timestamp in C# format (7 decimal places for fractional seconds)
        now = datetime.now(timezone.utc)
        # Format timestamp to match C# format: YYYY-MM-DDTHH:MM:SS.fffffffZ
        # Python's isoformat gives 6 decimal places, C# uses 7
        timestamp_base = now.strftime("%Y-%m-%dT%H:%M:%S")
        microseconds = now.microsecond
        # Pad microseconds to 7 digits (C# uses ticks, which has 7 decimal places)
        timestamp = f"{timestamp_base}.{microseconds:06d}0+00:00"

        # Build metadata exactly as C# CommandBus does (with same field order)
        metadata = {
            "Created": timestamp,
            "ClientHostName": socket.gethostname(),
            "$correlationId": command_id,
            "$causationId": command_id,
            "RecipientId": str(recipient_id),  # Where to route
            "SessionId": self.session_id,  # CommandBus session
            "UserId": None,  # Required by C# side, even if null
        }

        # Serialize command with PascalCase for EventStore
        if hasattr(command, "model_dump"):
            # Pydantic v2 model
            event_data = command.model_dump(by_alias=True, mode="json")
        elif hasattr(command, "dict"):
            # Pydantic v1 model (fallback)
            event_data = command.dict(by_alias=True)
        else:
            # Plain dict or other object
            event_data = command if isinstance(command, dict) else {"data": str(command)}

        # Get event type name
        event_type = command.__class__.__name__ if hasattr(command, "__class__") else "Command"

        # Create EventStore event
        new_event = NewEvent(
            type=event_type,
            data=json.dumps(event_data).encode("utf-8"),
            metadata=json.dumps(metadata).encode("utf-8"),
            content_type="application/json",
        )

        # Write to CommandBus input stream
        # C# handlers will read this and route based on RecipientId
        # Use the underlying EventStoreDBClient directly for raw events
        self.client._client.append_to_stream(  # noqa: SLF001
            stream_name=self.stream_in,
            events=[new_event],
            current_version=StreamState.ANY,
        )

    async def queue_async(
        self,
        recipient_id: Union[str, UUID],
        command: Union[Event, Any],  # noqa: ANN401
        fire_and_forget: bool = True,
        timeout: Optional[float] = None,
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
        if hasattr(self.client, "close"):
            self.client.close()

    async def __aenter__(self) -> "CommandBus":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Async context manager exit."""
        self.close()

    def __enter__(self) -> "CommandBus":
        """Sync context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Sync context manager exit."""
        self.close()
