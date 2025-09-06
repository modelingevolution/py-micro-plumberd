"""Metadata handling for py-micro-plumberd."""

import socket
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class Metadata:
    """Event metadata container with automatic enrichment."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize metadata with custom values.

        Args:
            **kwargs: Custom metadata key-value pairs
        """
        self._data = kwargs

    def enrich(self, event_id: str) -> Dict[str, Any]:
        """Enrich metadata with standard fields.

        Args:
            event_id: The event's unique identifier (used for correlation/causation)

        Returns:
            Complete metadata dictionary with standard fields
        """
        # Get current timestamp in ISO 8601 format with timezone
        now = datetime.now(timezone.utc).astimezone()
        created = now.isoformat()

        # Get hostname
        hostname = socket.gethostname()

        # Build metadata dictionary
        metadata = {
            "Created": created,
            "ClientHostName": hostname,
            "$correlationId": event_id,
            "$causationId": event_id,
        }

        # Add custom metadata
        metadata.update(self._data)

        return metadata

    @staticmethod
    def default() -> "Metadata":
        """Create default empty metadata."""
        return Metadata()
