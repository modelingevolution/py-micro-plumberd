# C# Integration Tests

These tests verify that events written by py-micro-plumberd can be correctly read by C# applications using the micro-plumberd framework.

## Prerequisites

- .NET 8.0 SDK
- EventStore running locally (or set EVENTSTORE_URL environment variable)
- Python with py-micro-plumberd installed

## Running the Tests

1. Ensure EventStore is running:
   ```bash
   docker run --name eventstore -it -p 2113:2113 -p 1113:1113 \
     eventstore/eventstore:latest --insecure --enable-atom-pub-over-http
   ```

2. Install py-micro-plumberd in development mode:
   ```bash
   cd ../..
   pip install -e .
   ```

3. Run the C# tests:
   ```bash
   dotnet test
   ```

## What the Tests Verify

1. **Event Data Compatibility**: Python events are correctly deserialized by C#
2. **Metadata Format**: Created timestamp and ClientHostName are preserved
3. **Stream Naming**: Category-StreamId format works across languages
4. **Event Ordering**: Multiple events maintain their order
5. **Property Name Mapping**: snake_case to PascalCase conversion works correctly

## Test Events

The tests use these event types that exist in both Python and C#:

- `RecordingFinished`: Contains recording metadata
- `TaskCreated`: Task creation with optional assignment
- `TaskCompleted`: Task completion with optional notes