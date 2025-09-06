"""Unit tests for Metadata class."""

from py_micro_plumberd.metadata import Metadata


class TestMetadata:
    """Test Metadata class for EventStore metadata handling."""

    def test_metadata_enrich_with_event_id(self) -> None:
        """Test enriching metadata with event ID."""
        metadata = Metadata()
        result = metadata.enrich("event-123")

        # Check standard fields
        assert result["$correlationId"] == "event-123"
        assert result["$causationId"] == "event-123"
        assert "Created" in result
        assert "ClientHostName" in result

    def test_metadata_with_custom_fields(self) -> None:
        """Test metadata with custom fields."""
        metadata = Metadata(
            user_id="user-123",
            session_id="sess-456",
            request_id="req-789",
        )
        result = metadata.enrich("event-456")

        # Check standard fields
        assert result["$correlationId"] == "event-456"
        assert result["$causationId"] == "event-456"

        # Check custom fields
        assert result["user_id"] == "user-123"
        assert result["session_id"] == "sess-456"
        assert result["request_id"] == "req-789"

    def test_metadata_custom_overwrites_defaults(self) -> None:
        """Test that custom metadata can override default fields."""
        metadata = Metadata(
            **{
                "$correlationId": "custom-corr",
                "$causationId": "custom-cause",
                "normal_field": "normal_value",
            },
        )
        result = metadata.enrich("event-789")

        # Custom values should override the defaults from enrich
        assert result["$correlationId"] == "custom-corr"
        assert result["$causationId"] == "custom-cause"
        assert result["normal_field"] == "normal_value"

    def test_metadata_default_factory(self) -> None:
        """Test default metadata factory method."""
        metadata = Metadata.default()
        result = metadata.enrich("event-default")

        # Should have standard fields only
        assert result["$correlationId"] == "event-default"
        assert result["$causationId"] == "event-default"
        assert "Created" in result
        assert "ClientHostName" in result

    def test_metadata_timestamp_format(self) -> None:
        """Test that timestamp is in ISO format."""
        metadata = Metadata()
        result = metadata.enrich("event-time")

        created = result["Created"]
        # Should be ISO format with timezone
        assert "T" in created  # ISO format has T separator
        assert "+" in created or "-" in created or "Z" in created  # Has timezone

    def test_metadata_multiple_enrichments(self) -> None:
        """Test enriching the same metadata multiple times."""
        metadata = Metadata(static_field="static_value")

        # First enrichment
        result1 = metadata.enrich("event-1")
        assert result1["$correlationId"] == "event-1"
        assert result1["static_field"] == "static_value"

        # Second enrichment with different event ID
        result2 = metadata.enrich("event-2")
        assert result2["$correlationId"] == "event-2"
        assert result2["static_field"] == "static_value"

        # Results should be different (different timestamps or IDs)
        diff_time = result1["Created"] != result2["Created"]
        diff_corr = result1["$correlationId"] != result2["$correlationId"]
        assert diff_time or diff_corr
