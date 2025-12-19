import json
import pytest
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestDateTimeGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        ts_metadata = TimestampShiftMetadata(left_shift_in_days=-30, right_shift_in_days=30)
        metadata = DateTimeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            additional_date_formats=["yyyy-MM-dd"],
            apply_constant_shift_to_document=True,
            metadata=ts_metadata,
            swaps={"date1": "date2"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "DateTime"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["scrambleUnrecognizedDates"] is False
        assert parsed["additionalDateFormats"] == ["yyyy-MM-dd"]
        assert parsed["applyConstantShiftToDocument"] is True
        assert parsed["metadata"]["leftShiftInDays"] == -30
        assert parsed["metadata"]["rightShiftInDays"] == 30

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = DateTimeGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "DateTimeGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = DateTimeGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = DateTimeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.additional_date_formats == original.additional_date_formats
        assert restored.apply_constant_shift_to_document == original.apply_constant_shift_to_document
        assert restored.metadata.left_shift_in_days == original.metadata.left_shift_in_days
        assert restored.metadata.right_shift_in_days == original.metadata.right_shift_in_days

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        ts_metadata = TimestampShiftMetadata(
            left_shift_in_days=-100,
            right_shift_in_days=100,
            swaps={"ts_key": "ts_val"}
        )
        original = DateTimeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            additional_date_formats=["format1", "format2"],
            apply_constant_shift_to_document=True,
            metadata=ts_metadata,
            swaps={"outer": "swap"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = DateTimeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.DateTime
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.scramble_unrecognized_dates is False
        assert restored.additional_date_formats == ["format1", "format2"]
        assert restored.apply_constant_shift_to_document is True
        assert restored.metadata.left_shift_in_days == -100
        assert restored.metadata.right_shift_in_days == 100
        assert restored.metadata.swaps == {"ts_key": "ts_val"}
        assert restored.swaps == {"outer": "swap"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = DateTimeGeneratorMetadata(
            additional_date_formats=["yyyy-MM-dd"],
            apply_constant_shift_to_document=True
        )

        assert metadata.additional_date_formats == ["yyyy-MM-dd"]
        assert metadata.apply_constant_shift_to_document is True
        assert metadata.custom_generator == GeneratorType.DateTime

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = DateTimeGeneratorMetadata()
        metadata.additional_date_formats = ["new-format"]
        metadata.apply_constant_shift_to_document = True

        assert metadata.additional_date_formats == ["new-format"]
        assert metadata["additionalDateFormats"] == ["new-format"]
        assert metadata.apply_constant_shift_to_document is True
        assert metadata["applyConstantShiftToDocument"] is True

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = DateTimeGeneratorMetadata(additional_date_formats=["test"])

        assert metadata["additionalDateFormats"] == ["test"]
        assert metadata["_type"] == "DateTimeGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = DateTimeGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "DateTimeGeneratorMetadata"
        assert "metadata" in payload

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = DateTimeGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_nested_metadata_is_serializable(self):
        """Nested TimestampShiftMetadata should serialize correctly."""
        ts_metadata = TimestampShiftMetadata(left_shift_in_days=-50, right_shift_in_days=50)
        metadata = DateTimeGeneratorMetadata(metadata=ts_metadata)
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["metadata"]["leftShiftInDays"] == -50
        assert parsed["metadata"]["rightShiftInDays"] == 50
        assert parsed["metadata"]["_type"] == "TimestampShiftMetadata"

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            DateTimeGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
