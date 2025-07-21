namespace PyMicroPlumberd.IntegrationTests;

/// <summary>
/// Event definitions matching the Python test events
/// </summary>
public record RecordingFinished(string RecordingId, double Duration, string FilePath);

public record TaskCreated(string Title, string Description, string? AssignedTo = null);

public record TaskCompleted(string CompletedBy, string? CompletionNotes = null);