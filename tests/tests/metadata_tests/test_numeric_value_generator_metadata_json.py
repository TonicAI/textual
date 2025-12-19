import json
import pytest
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestNumericValueGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = NumericValueGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_oracle_integer_pk_generator=True,
            swaps={"123": "456"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "NumericValue"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["useOracleIntegerPkGenerator"] is True
        assert parsed["swaps"] == {"123": "456"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = NumericValueGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "NumericValueGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = NumericValueGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = NumericValueGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.use_oracle_integer_pk_generator == original.use_oracle_integer_pk_generator
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = NumericValueGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_oracle_integer_pk_generator=True,
            swaps={"val1": "val2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = NumericValueGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.NumericValue
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.use_oracle_integer_pk_generator is True
        assert restored.swaps == {"val1": "val2"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = NumericValueGeneratorMetadata(use_oracle_integer_pk_generator=True)

        assert metadata.use_oracle_integer_pk_generator is True
        assert metadata.custom_generator == GeneratorType.NumericValue

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = NumericValueGeneratorMetadata()
        metadata.use_oracle_integer_pk_generator = True

        assert metadata.use_oracle_integer_pk_generator is True
        assert metadata["useOracleIntegerPkGenerator"] is True

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = NumericValueGeneratorMetadata(use_oracle_integer_pk_generator=True)

        assert metadata["useOracleIntegerPkGenerator"] is True
        assert metadata["_type"] == "NumericValueGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = NumericValueGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "NumericValueGeneratorMetadata"
        assert payload["customGenerator"] == GeneratorType.NumericValue

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = NumericValueGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            NumericValueGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
