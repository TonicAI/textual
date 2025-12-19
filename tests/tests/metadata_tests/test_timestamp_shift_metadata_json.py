import json
import pytest
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata


class TestTimestampShiftMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = TimestampShiftMetadata(
            left_shift_in_days=-30,
            right_shift_in_days=30,
            swaps={"ts1": "ts2"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["leftShiftInDays"] == -30
        assert parsed["rightShiftInDays"] == 30
        assert parsed["swaps"] == {"ts1": "ts2"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = TimestampShiftMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "TimestampShiftMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = TimestampShiftMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = TimestampShiftMetadata.from_payload(parsed)

        assert restored.left_shift_in_days == original.left_shift_in_days
        assert restored.right_shift_in_days == original.right_shift_in_days
        assert restored.swaps == original.swaps
        assert restored.time_stamp_shift_in_days == original.time_stamp_shift_in_days

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = TimestampShiftMetadata(
            left_shift_in_days=-100,
            right_shift_in_days=100,
            swaps={"key": "value"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = TimestampShiftMetadata.from_payload(parsed)

        assert restored.left_shift_in_days == -100
        assert restored.right_shift_in_days == 100
        assert restored.swaps == {"key": "value"}

    def test_json_roundtrip_with_deprecated_field(self):
        """Round-trip serialization preserves deprecated time_stamp_shift_in_days."""
        with pytest.warns(UserWarning, match="time_stamp_shift_in_days"):
            original = TimestampShiftMetadata(time_stamp_shift_in_days=50)

        json_str = json.dumps(original)
        parsed = json.loads(json_str)

        with pytest.warns(UserWarning, match="time_stamp_shift_in_days"):
            restored = TimestampShiftMetadata.from_payload(parsed)

        assert restored.time_stamp_shift_in_days == 50

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = TimestampShiftMetadata(
            left_shift_in_days=-50,
            right_shift_in_days=50
        )

        assert metadata.left_shift_in_days == -50
        assert metadata.right_shift_in_days == 50

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = TimestampShiftMetadata()
        metadata.left_shift_in_days = -200
        metadata.right_shift_in_days = 200

        assert metadata.left_shift_in_days == -200
        assert metadata["leftShiftInDays"] == -200
        assert metadata.right_shift_in_days == 200
        assert metadata["rightShiftInDays"] == 200

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = TimestampShiftMetadata(left_shift_in_days=-10)

        assert metadata["leftShiftInDays"] == -10
        assert metadata["_type"] == "TimestampShiftMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = TimestampShiftMetadata(left_shift_in_days=-25, right_shift_in_days=25)
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["leftShiftInDays"] == -25
        assert payload["rightShiftInDays"] == 25
        assert payload["_type"] == "TimestampShiftMetadata"

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = TimestampShiftMetadata()

        assert isinstance(metadata, dict)

    def test_deprecated_field_not_in_json_when_none(self):
        """timestampShiftInDays should not appear in JSON when None."""
        metadata = TimestampShiftMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert "timestampShiftInDays" not in parsed
