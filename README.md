# py-micro-plumberd

A lightweight Python library for writing events to EventStore, designed for seamless interoperability with the .NET micro-plumberd framework. This library ensures that events written from Python can be read and processed by C# applications using micro-plumberd.

## Features

- Simple event definition with automatic ID generation (lowercase UUID with dashes)
- Stream naming convention: `{Category}-{StreamId}`
- Automatic metadata enrichment (Created timestamp, ClientHostName)
- EventStore client for appending events
- Full compatibility with C# micro-plumberd event format

## Installation

```bash
pip install py-micro-plumberd
```

## Quick Start

### Define an Event

```python
from py_micro_plumberd import Event
from datetime import datetime
import uuid

class RecordingFinished(Event):
    def __init__(self, recording_id: str, duration: float, file_path: str):
        super().__init__()
        self.recording_id = recording_id
        self.duration = duration
        self.file_path = file_path
```

### Append Events to EventStore

```python
from py_micro_plumberd import EventStoreClient, StreamName

# Create client
client = EventStoreClient("esdb://localhost:2113?tls=false")

# Create an event
event = RecordingFinished(
    recording_id="rec-123",
    duration=120.5,
    file_path="/recordings/rec-123.mp4"
)

# Define stream
stream = StreamName(category="Recording", stream_id="b27f9322-7d73-4d98-a605-a731a2c373c6")

# Append event
client.append_to_stream(stream, event)
```

## Core Concepts

### Events

All events must inherit from the `Event` base class, which automatically:
- Generates a unique ID (UUID) for each event instance
- Provides serialization support
- Enables metadata enrichment

### Stream Naming

Streams follow the pattern `{Category}-{StreamId}`:
- **Category**: Logical grouping of events (e.g., "Recording", "User", "Order")
- **StreamId**: Unique identifier for the stream instance (typically a UUID)

Example: `Recording-b27f9322-7d73-4d98-a605-a731a2c373c6`

### Metadata

Each event is automatically enriched with metadata:
- **Created**: ISO 8601 timestamp of when the event was created
- **ClientHostName**: Hostname of the machine creating the event
- **\$correlationId$**: Same as TEvent.Id
- **\$causationId**: Same sa TEvent.Id

## Advanced Usage

### Custom Metadata

```python
from py_micro_plumberd import Event, Metadata

class UserRegistered(Event):
    def __init__(self, email: str, username: str):
        super().__init__()
        self.email = email
        self.username = username


client.append_to_stream(stream, event)
```

### Reading Events in C#

Events written by py-micro-plumberd can be read using the .NET micro-plumberd framework:

```csharp
using MicroPlumberd;

// Define matching event class
public record RecordingFinished(string RecordingId, double Duration, string FilePath);

// Read events using micro-plumberd
var plumber = serviceProvider.GetRequiredService<IPlumber>();
var events = await plumber.ReadStream("Recording-b27f9322-7d73-4d98-a605-a731a2c373c6");

foreach (var evt in events)
{
    if (evt.Event is RecordingFinished recording)
    {
        Console.WriteLine($"Recording {recording.RecordingId} finished");
        Console.WriteLine($"Duration: {recording.Duration} seconds");
        Console.WriteLine($"Created: {evt.Metadata.Created}");
    }
}
```

## Configuration

### Connection String

The EventStore connection string supports various formats:

```python
# Insecure connection
client = EventStoreClient("esdb://localhost:2113?tls=false")

# Secure connection
client = EventStoreClient("esdb://localhost:2113")

# With credentials
client = EventStoreClient("esdb://admin:changeit@localhost:2113")
```

### Client Options

```python
client = EventStoreClient(
    connection_string="esdb://localhost:2113",
    default_deadline=30,  # seconds
    keep_alive_interval=10,  # seconds
    keep_alive_timeout=10  # seconds
)
```

## Examples

### Complete Example: Task Management System

```python
from py_micro_plumberd import Event, EventStoreClient, StreamName
from datetime import datetime

# Define events
class TaskCreated(Event):
    def __init__(self, title: str, description: str):
        super().__init__()
        self.title = title
        self.description = description

class TaskCompleted(Event):
    def __init__(self, completed_by: str, completion_notes: str = None):
        super().__init__()
        self.completed_by = completed_by
        self.completion_notes = completion_notes

def main():
    # Setup client
    client = EventStoreClient("esdb://localhost:2113?tls=false")
    
    # Create task stream
    task_id = "7d73-4d98-a605-a731a2c373c6"
    stream = StreamName(category="Task", stream_id=task_id)
    
    # Create task
    created_event = TaskCreated(
        title="Implement py-micro-plumberd",
        description="Create Python version of micro-plumberd"
    )
    client.append_to_stream(stream, created_event)
    
    # Complete task
    completed_event = TaskCompleted(
        completed_by="developer@example.com",
        completion_notes="Successfully implemented core functionality"
    )
    client.append_to_stream(stream, completed_event)
    
    print(f"Events written to stream: {stream}")
    print("These events can now be read using C# micro-plumberd")

if __name__ == "__main__":
    main()
```

## Requirements

- Python 3.8+
- EventStore 20.6+
- esdbclient

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Integration Testing

The library includes integration tests to ensure compatibility between Python and C#:

```bash
# Run Python tests
pytest tests/

# Run C# integration tests (requires .NET SDK)
cd tests/csharp
dotnet test
```

## Event Format Compatibility

To ensure C# compatibility, events written by py-micro-plumberd follow these conventions:

1. **Event ID**: Lowercase UUID with dashes (e.g., `"3fa85f64-5717-4562-b3fc-2c963f66afa6"`)
2. **Metadata Format**: JSON object with:
   - `Created`: ISO 8601 timestamp (e.g., `"2025-07-13T18:22:19.2192669+02:00"`)
   - `ClientHostName`: Machine hostname (e.g., `"MARS"`)
3. **Event Data**: JSON serialized with property names in PascalCase to match C# conventions

## Links

- [EventStore Documentation](https://eventstore.com/docs/)
- [Original micro-plumberd (.NET)](https://github.com/modelingevolution/micro-plumberd)