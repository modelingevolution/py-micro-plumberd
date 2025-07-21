"""py-micro-plumberd: A lightweight Python library for writing events to EventStore."""

from .event import Event
from .metadata import Metadata
from .stream import StreamName
from .client import EventStoreClient

__version__ = "0.1.1"
__all__ = ["Event", "Metadata", "StreamName", "EventStoreClient"]