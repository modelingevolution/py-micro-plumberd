using EventStore.Client;
using Grpc.Core;
using MicroPlumberd;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System.Diagnostics;
using System.Text.Json;
using MicroPlumberd.Services;
using Xunit;
using Xunit.Abstractions;

namespace PyMicroPlumberd.IntegrationTests;

public class ReadPythonEventsTests : IAsyncLifetime
{
    private readonly ITestOutputHelper _output;
    private readonly string _eventStoreUrl;
    private readonly string _streamId;
    private IHost? _host;
    private IPlumber? _plumber;

    public ReadPythonEventsTests(ITestOutputHelper output)
    {
        _output = output;
        _eventStoreUrl = Environment.GetEnvironmentVariable("EVENTSTORE_URL") ?? "esdb://localhost:2113?tls=false";
        _streamId = Guid.NewGuid().ToString();
    }

    public async Task InitializeAsync()
    {
        var builder = Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddLogging(logging => logging.AddConsole());
                
                // Configure EventStore
                var settings = EventStoreClientSettings.Create(_eventStoreUrl);
                services.AddSingleton(settings);
                
                // Add MicroPlumberd
                services.AddPlumberd();
            });

        _host = builder.Build();
        await _host.StartAsync();
        
        _plumber = _host.Services.GetRequiredService<IPlumber>();
    }

    public async Task DisposeAsync()
    {
        if (_host != null)
        {
            await _host.StopAsync();
            _host.Dispose();
        }
    }

    [Fact]
    public async Task Should_Read_RecordingFinished_Event_Written_By_Python()
    {
        // Arrange
        var streamName = $"Recording-{_streamId}";
        
        // Write event using Python
        await WritePythonEvent(streamName, "RecordingFinished", new
        {
            recording_id = "rec-123",
            duration = 120.5,
            file_path = "/recordings/rec-123.mp4"
        });

        // Act - Read using micro-plumberd
        var events = await _plumber!.ReadEventsOfType<RecordingFinished>(streamName).ToListAsync();

        // Assert
        Assert.Single(events);
        var (evt,metadata)= events[0];

        
        Assert.Equal("rec-123", evt.RecordingId);
        Assert.Equal(120.5, evt.Duration);
        Assert.Equal("/recordings/rec-123.mp4", evt.FilePath);
        
        // Verify metadata
        Assert.NotNull(metadata);
        Assert.True(metadata.Created() > DateTimeOffset.MinValue);
        Assert.NotEmpty(metadata.Data.GetProperty("ClientHostName").GetString());
        
        _output.WriteLine($"Successfully read RecordingFinished event from stream {streamName}");
        _output.WriteLine($"Event ID: {metadata.EventId}");
        _output.WriteLine($"Created: {metadata.Created()}");
        _output.WriteLine($"ClientHostName: {metadata.Data.GetProperty("ClientHostName").GetString()}");
    }

    

    private async Task WritePythonEvent(string streamName, string eventType, object eventData, string? eventId = null)
    {
        // Find the project root by looking for the venv directory
        // This is the py-micro-plumberd root directory
        var src = Environment.GetEnvironmentVariable("MODELING_EVOLUTION_SRC", EnvironmentVariableTarget.Process);
        var projectRoot = Path.Combine(src, "py-micro-plumberd");
        var venvPython = Path.Combine(projectRoot, "venv", "bin", "python3");
        
        if (!File.Exists(venvPython))
        {
            throw new FileNotFoundException($"Virtual environment Python not found at: {venvPython}. Make sure to run 'python3 -m venv venv && source venv/bin/activate && pip install -e .' in the project root.");
        }
        
        // Create Python script to write event
        var pythonScript = $@"
from py_micro_plumberd import Event, EventStoreClient, StreamName

class {eventType}(Event):
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)
        {(eventId != null ? $"self.id = '{eventId}'" : "")}

# Create event
event = {eventType}(**{JsonSerializer.Serialize(eventData)})

# Parse stream name
stream_parts = '{streamName}'.split('-', 1)
stream = StreamName(category=stream_parts[0], stream_id=stream_parts[1])

# Write to EventStore
client = EventStoreClient('{_eventStoreUrl}')
try:
    client.append_to_stream(stream, event)
    print(f'Successfully wrote {eventType} event to {streamName}')
finally:
    client.close()
";

        var tempFile = Path.GetTempFileName() + ".py";
        await File.WriteAllTextAsync(tempFile, pythonScript);

        try
        {
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = venvPython,  // Use the venv Python directly
                    Arguments = tempFile,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = projectRoot  // Set working directory to project root
                }
            };

            _output.WriteLine($"Running: {venvPython} {tempFile}");

            process.Start();
            
            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            
            await process.WaitForExitAsync();

            if (!string.IsNullOrEmpty(output))
            {
                _output.WriteLine($"Python stdout: {output}");
            }

            if (process.ExitCode != 0)
            {
                _output.WriteLine($"Python stderr: {error}");
                throw new Exception($"Python script failed with exit code {process.ExitCode}: {error}");
            }
        }
        finally
        {
            File.Delete(tempFile);
        }
    }
}