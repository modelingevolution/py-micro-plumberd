"""py-micro-plumberd: A lightweight Python library for writing events to EventStore."""

from .client import EventStoreClient
from .command_bus import CommandBus
from .event import Event
from .metadata import Metadata
from .stream import StreamName

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__all__ = ["CommandBus", "Event", "EventStoreClient", "Metadata", "StreamName", "__version__"]
