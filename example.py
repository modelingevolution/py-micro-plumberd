"""Example usage of py-micro-plumberd with Pydantic v2."""

from typing import Optional

from py_micro_plumberd import Event, EventStoreClient, StreamName


# Define your events using Pydantic v2 style
class RecordingFinished(Event):
    """Event emitted when a recording is finished."""
    recording_id: str
    duration: float
    file_path: str


class RecordingStarted(Event):
    """Event emitted when a recording starts."""
    recording_id: str
    camera_id: str
    resolution: Optional[str] = None


def main():
    # Create EventStore client
    client = EventStoreClient("esdb://localhost:2113?tls=false")
    
    # Define the stream
    stream = StreamName(category="Recording", stream_id="b27f9322-7d73-4d98-a605-a731a2c373c6")
    
    try:
        # Append a RecordingStarted event (using Pythonic snake_case)
        started_event = RecordingStarted(
            recording_id="rec-123",
            camera_id="camera-01",
            resolution="1920x1080"
        )
        
        print(f"Writing RecordingStarted event with ID: {started_event.id}")
        print(f"  Camera: {started_event.camera_id}")  # Pythonic access
        print(f"  Resolution: {started_event.resolution}")
        
        client.append_to_stream(stream, started_event)
        
        # Simulate some recording time
        import time
        time.sleep(1)
        
        # Append a RecordingFinished event
        finished_event = RecordingFinished(
            recording_id="rec-123",
            duration=120.5,
            file_path="/recordings/rec-123.mp4"
        )
        
        print(f"\nWriting RecordingFinished event with ID: {finished_event.id}")
        print(f"  Duration: {finished_event.duration} seconds")  # Pythonic access
        print(f"  File: {finished_event.file_path}")
        
        client.append_to_stream(stream, finished_event)
        
        print(f"\nEvents successfully written to stream: {stream}")
        print("These events are serialized as PascalCase for C# micro-plumberd compatibility!")
        print("\nExample serialized event:")
        print(finished_event.model_dump(by_alias=True))  # Shows PascalCase output
        
    finally:
        client.close()


if __name__ == "__main__":
    main()