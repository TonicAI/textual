import json
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestBaseDateTimeGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = BaseDateTimeGeneratorMetadata(
            custom_generator=GeneratorType.DateTime,
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            swaps={"date1": "date2"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "DateTime"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["scrambleUnrecognizedDates"] is False
        assert parsed["swaps"] == {"date1": "date2"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = BaseDateTimeGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "BaseDateTimeGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = BaseDateTimeGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = BaseDateTimeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = BaseDateTimeGeneratorMetadata(
            custom_generator=GeneratorType.PersonAge,
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            swaps={"a": "b"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = BaseDateTimeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.swaps == original.swaps

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = BaseDateTimeGeneratorMetadata(
            scramble_unrecognized_dates=False
        )

        assert metadata.scramble_unrecognized_dates is False

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = BaseDateTimeGeneratorMetadata()
        metadata.scramble_unrecognized_dates = False

        assert metadata.scramble_unrecognized_dates is False
        assert metadata["scrambleUnrecognizedDates"] is False

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = BaseDateTimeGeneratorMetadata(scramble_unrecognized_dates=False)

        assert metadata["scrambleUnrecognizedDates"] is False
        assert metadata["_type"] == "BaseDateTimeGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = BaseDateTimeGeneratorMetadata(scramble_unrecognized_dates=False)
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["scrambleUnrecognizedDates"] is False
        assert payload["_type"] == "BaseDateTimeGeneratorMetadata"

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = BaseDateTimeGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_inherits_base_metadata_properties(self):
        """Should inherit properties from BaseMetadata."""
        metadata = BaseDateTimeGeneratorMetadata(
            custom_generator=GeneratorType.DateTime,
            generator_version=GeneratorVersion.V2,
            swaps={"key": "value"}
        )

        assert metadata.custom_generator == GeneratorType.DateTime
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"key": "value"}
