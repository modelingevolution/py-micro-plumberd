"""Unit tests for CommandBus class."""

import json
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from py_micro_plumberd.command_bus import CommandBus
from py_micro_plumberd.event import Event


class TestCommand(Event):
    """Test command for CommandBus tests."""

    title: str
    priority: int


class TestCommandBus:
    """Test CommandBus for micro-plumberd compatibility."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock EventStoreClient."""
        client = MagicMock()
        client._client = MagicMock()  # noqa: SLF001
        client._client.append_to_stream = MagicMock()  # noqa: SLF001
        return client

    @pytest.fixture
    def command_bus(self, mock_client: MagicMock) -> CommandBus:
        """Create CommandBus with mock client."""
        return CommandBus(mock_client)

    def test_command_bus_initialization(self, command_bus: CommandBus) -> None:
        """Test CommandBus initializes with session ID and streams."""
        assert command_bus.session_id is not None
        assert command_bus.stream_in.startswith(">SessionIn-")
        assert command_bus.stream_out.startswith(">SessionOut-")

        # Verify session ID is a valid UUID
        UUID(command_bus.session_id)  # Will raise if invalid

    async def test_send_async_fire_and_forget(
        self,
        command_bus: CommandBus,
        mock_client: MagicMock,
    ) -> None:
        """Test sending a fire-and-forget command."""
        recipient_id = "ui-session-123"
        command = TestCommand(title="Test Task", priority=1)

        await command_bus.send_async(recipient_id, command, fire_and_forget=True)

        # Verify append_to_stream was called
        mock_client._client.append_to_stream.assert_called_once()  # noqa: SLF001

        # Get the call arguments
        call_args = mock_client._client.append_to_stream.call_args  # noqa: SLF001
        assert call_args.kwargs["stream_name"] == command_bus.stream_in

        # Verify event structure
        events = call_args.kwargs["events"]
        assert len(events) == 1
        event = events[0]
        assert event.type == "TestCommand"

    async def test_send_async_not_fire_and_forget_raises(self, command_bus: CommandBus) -> None:
        """Test that non-fire-and-forget commands raise NotImplementedError."""
        command = TestCommand(title="Test", priority=1)

        with pytest.raises(NotImplementedError, match="not supported"):
            await command_bus.send_async("recipient-123", command, fire_and_forget=False)

    async def test_queue_async_delegates_to_send(
        self,
        command_bus: CommandBus,
        mock_client: MagicMock,
    ) -> None:
        """Test that queue_async delegates to send_async."""
        recipient_id = "ui-session-456"
        command = TestCommand(title="Queued Task", priority=2)

        await command_bus.queue_async(recipient_id, command)

        # Verify the command was sent
        mock_client._client.append_to_stream.assert_called_once()  # noqa: SLF001

    @patch("socket.gethostname")
    async def test_metadata_format(
        self,
        mock_hostname: MagicMock,
        command_bus: CommandBus,
        mock_client: MagicMock,
    ) -> None:
        """Test that metadata is formatted correctly for C# compatibility."""
        mock_hostname.return_value = "test-host"

        recipient_id = "ui-session-789"
        command = TestCommand(title="Meta Test", priority=3)

        await command_bus.send_async(recipient_id, command)

        # Get the metadata from the call
        call_args = mock_client._client.append_to_stream.call_args  # noqa: SLF001
        events = call_args.kwargs["events"]
        event = events[0]

        # Parse metadata
        metadata = json.loads(event.metadata)

        # Verify metadata fields
        assert metadata["$correlationId"] == str(command.id)
        assert metadata["$causationId"] == str(command.id)
        assert metadata["SessionId"] == command_bus.session_id
        assert metadata["RecipientId"] == recipient_id
        assert metadata["ClientHostName"] == "test-host"
        assert "Created" in metadata
        assert "UserId" in metadata
        assert metadata["UserId"] is None
        
        # Verify timestamp format (7 decimal places for C# compatibility)
        created = metadata["Created"]
        # Should have format: YYYY-MM-DDTHH:MM:SS.fffffffZ
        assert "T" in created  # ISO format
        assert "." in created  # Has fractional seconds
        # Check for 7 decimal places
        fractional_part = created.split(".")[1].split("+")[0]
        assert len(fractional_part) == 7, f"Expected 7 decimal places, got {len(fractional_part)}: {created}"
        
        # Verify field order (Created should be first)
        keys_list = list(metadata.keys())
        assert keys_list[0] == "Created", f"Expected 'Created' first, got {keys_list[0]}"

    async def test_command_data_pascal_case(
        self,
        command_bus: CommandBus,
        mock_client: MagicMock,
    ) -> None:
        """Test that command data is serialized to PascalCase."""
        command = TestCommand(title="Pascal Test", priority=5)

        await command_bus.send_async("recipient", command)

        # Get the data from the call
        call_args = mock_client._client.append_to_stream.call_args  # noqa: SLF001
        events = call_args.kwargs["events"]
        event = events[0]

        # Parse data
        data = json.loads(event.data)

        # Verify PascalCase conversion
        assert "Title" in data
        assert data["Title"] == "Pascal Test"
        assert "Priority" in data
        assert data["Priority"] == 5  # noqa: PLR2004
        assert "Id" in data

    def test_context_manager(self, mock_client: MagicMock) -> None:
        """Test CommandBus as context manager."""
        with CommandBus(mock_client) as bus:
            assert bus is not None
            assert isinstance(bus, CommandBus)

        # Verify close was called
        mock_client.close.assert_called_once()

    async def test_async_context_manager(self, mock_client: MagicMock) -> None:
        """Test CommandBus as async context manager."""
        async with CommandBus(mock_client) as bus:
            assert bus is not None
            assert isinstance(bus, CommandBus)

        # Verify close was called
        mock_client.close.assert_called_once()

    async def test_send_with_uuid_recipient(
        self,
        command_bus: CommandBus,
        mock_client: MagicMock,
    ) -> None:
        """Test sending command with UUID as recipient ID."""
        recipient_uuid = UUID("12345678-1234-5678-1234-567812345678")
        command = TestCommand(title="UUID Test", priority=1)

        await command_bus.send_async(recipient_uuid, command)

        # Verify it was sent and recipient ID is string
        call_args = mock_client._client.append_to_stream.call_args  # noqa: SLF001
        events = call_args.kwargs["events"]

        metadata = json.loads(events[0].metadata)
        assert metadata["RecipientId"] == str(recipient_uuid)
