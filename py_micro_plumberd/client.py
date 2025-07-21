"""EventStore client for py-micro-plumberd."""

import json
from typing import Any, Dict, Optional, Union

from esdbclient import EventStoreDBClient, NewEvent, StreamState

from .event import Event
from .metadata import Metadata
from .stream import StreamName


class EventStoreClient:
    """Client for appending events to EventStore."""
    
    def __init__(
        self,
        connection_string: str,
        default_deadline: Optional[float] = None,
        keep_alive_interval: Optional[int] = None,
        keep_alive_timeout: Optional[int] = None,
    ) -> None:
        """Initialize EventStore client.
        
        Args:
            connection_string: EventStore connection string (e.g., "esdb://localhost:2113?tls=false")
            default_deadline: Default deadline for operations in seconds
            keep_alive_interval: Keep alive interval in seconds
            keep_alive_timeout: Keep alive timeout in seconds
        """
        # EventStoreDBClient doesn't support these parameters directly in __init__
        # Just pass the URI for now
        self._client = EventStoreDBClient(uri=connection_string)
    
    def append_to_stream(
        self,
        stream: Union[str, StreamName],
        event: Event,
        metadata: Optional[Metadata] = None,
        expected_position: Optional[int] = None,
    ) -> int:
        """Append an event to a stream.
        
        Args:
            stream: Stream name or StreamName object
            event: Event to append
            metadata: Optional custom metadata
            expected_position: Expected stream position for optimistic concurrency
            
        Returns:
            The commit position of the appended event
        """
        # Convert stream to string if needed
        stream_name = str(stream) if isinstance(stream, StreamName) else stream
        
        # Get event type name
        event_type = event.__class__.__name__
        
        # Prepare metadata
        if metadata is None:
            metadata = Metadata.default()
        
        enriched_metadata = metadata.enrich(event.id)
        
        # Convert event to data
        event_data = event.to_dict()
        
        # Create NewEvent for EventStore
        new_event = NewEvent(
            type=event_type,
            data=json.dumps(event_data).encode('utf-8'),
            metadata=json.dumps(enriched_metadata).encode('utf-8'),
            content_type="application/json",
        )
        
        # Determine expected state
        if expected_position is not None:
            current_position = StreamState(stream_position=expected_position)
        else:
            current_position = StreamState.ANY
        
        # Append to stream
        commit_position = self._client.append_to_stream(
            stream_name=stream_name,
            events=[new_event],
            current_version=current_position,
        )
        
        return commit_position
    
    def close(self) -> None:
        """Close the client connection."""
        self._client.close()
    
    def __enter__(self) -> "EventStoreClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()