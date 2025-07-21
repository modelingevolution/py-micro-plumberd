"""Example usage of py-micro-plumberd."""

from py_micro_plumberd import Event, EventStoreClient, StreamName


# Define your events
class RecordingFinished(Event):
    def __init__(self, recording_id: str, duration: float, file_path: str):
        super().__init__()
        self.recording_id = recording_id
        self.duration = duration
        self.file_path = file_path


class RecordingStarted(Event):
    def __init__(self, recording_id: str, camera_id: str):
        super().__init__()
        self.recording_id = recording_id
        self.camera_id = camera_id


def main():
    # Create EventStore client
    client = EventStoreClient("esdb://localhost:2113?tls=false")
    
    # Define the stream
    stream = StreamName(category="Recording", stream_id="b27f9322-7d73-4d98-a605-a731a2c373c6")
    
    try:
        # Append a RecordingStarted event
        started_event = RecordingStarted(
            recording_id="rec-123",
            camera_id="camera-01"
        )
        print(f"Writing RecordingStarted event with ID: {started_event.id}")
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
        
        print(f"Writing RecordingFinished event with ID: {finished_event.id}")
        client.append_to_stream(stream, finished_event)
        
        print(f"\nEvents successfully written to stream: {stream}")
        print("These events can now be read using C# micro-plumberd!")
        
    finally:
        client.close()


if __name__ == "__main__":
    main()