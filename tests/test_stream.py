"""Unit tests for StreamName class."""

import pytest

from py_micro_plumberd.stream import StreamName


class TestStreamName:
    """Test StreamName formatting and parsing."""

    def test_stream_name_creation(self) -> None:
        """Test creating a StreamName with valid category and ID."""
        stream = StreamName(category="Recording", stream_id="12345")
        assert stream.category == "Recording"
        assert stream.stream_id == "12345"

    def test_stream_name_str_format(self) -> None:
        """Test that StreamName formats correctly as string."""
        stream = StreamName(category="User", stream_id="abc-123")
        assert str(stream) == "User-abc-123"

    def test_stream_name_repr(self) -> None:
        """Test StreamName repr for debugging."""
        stream = StreamName(category="Order", stream_id="xyz-789")
        expected = "StreamName(category='Order', stream_id='xyz-789')"
        assert repr(stream) == expected

    def test_empty_category_raises_error(self) -> None:
        """Test that empty category raises ValueError."""
        with pytest.raises(ValueError, match="Category cannot be empty"):
            StreamName(category="", stream_id="123")

    def test_empty_stream_id_raises_error(self) -> None:
        """Test that empty stream ID raises ValueError."""
        with pytest.raises(ValueError, match="Stream ID cannot be empty"):
            StreamName(category="Test", stream_id="")

    def test_parse_valid_stream_name(self) -> None:
        """Test parsing a valid stream name string."""
        stream = StreamName.parse("Recording-12345")
        assert stream.category == "Recording"
        assert stream.stream_id == "12345"

    def test_parse_stream_name_with_dashes_in_id(self) -> None:
        """Test parsing stream name where ID contains dashes."""
        stream = StreamName.parse("User-abc-def-123")
        assert stream.category == "User"
        assert stream.stream_id == "abc-def-123"

    def test_parse_stream_name_with_uuid(self) -> None:
        """Test parsing stream name with UUID as ID."""
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        stream = StreamName.parse(f"Session-{uuid}")
        assert stream.category == "Session"
        assert stream.stream_id == uuid

    def test_parse_invalid_format_no_dash(self) -> None:
        """Test parsing invalid stream name without dash."""
        with pytest.raises(ValueError, match="Invalid stream name format: InvalidStream"):
            StreamName.parse("InvalidStream")

    def test_parse_invalid_format_empty_string(self) -> None:
        """Test parsing empty string raises error."""
        with pytest.raises(ValueError, match="Invalid stream name format: "):
            StreamName.parse("")

    def test_round_trip_parse_and_str(self) -> None:
        """Test that parsing and converting back to string works."""
        original = "TestCategory-test-id-with-dashes"
        stream = StreamName.parse(original)
        assert str(stream) == original

    def test_special_stream_names(self) -> None:
        """Test special stream name formats used by CommandBus."""
        # Test session input stream
        session_in = StreamName(category=">SessionIn", stream_id="abc-123")
        assert str(session_in) == ">SessionIn-abc-123"

        # Test session output stream
        session_out = StreamName(category=">SessionOut", stream_id="abc-123")
        assert str(session_out) == ">SessionOut-abc-123"

    def test_parse_special_stream_names(self) -> None:
        """Test parsing special stream names with > prefix."""
        stream_in = StreamName.parse(">SessionIn-12345")
        assert stream_in.category == ">SessionIn"
        assert stream_in.stream_id == "12345"
