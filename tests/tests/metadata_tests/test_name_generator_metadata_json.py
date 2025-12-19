import json
import pytest
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestNameGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = NameGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            is_consistency_case_sensitive=True,
            preserve_gender=True,
            swaps={"John": "Jane"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "Name"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["isConsistencyCaseSensitive"] is True
        assert parsed["preserveGender"] is True
        assert parsed["swaps"] == {"John": "Jane"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = NameGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "NameGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = NameGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = NameGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.is_consistency_case_sensitive == original.is_consistency_case_sensitive
        assert restored.preserve_gender == original.preserve_gender
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = NameGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            is_consistency_case_sensitive=True,
            preserve_gender=True,
            swaps={"name1": "name2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = NameGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.Name
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.is_consistency_case_sensitive is True
        assert restored.preserve_gender is True
        assert restored.swaps == {"name1": "name2"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = NameGeneratorMetadata(
            is_consistency_case_sensitive=True,
            preserve_gender=True
        )

        assert metadata.is_consistency_case_sensitive is True
        assert metadata.preserve_gender is True
        assert metadata.custom_generator == GeneratorType.Name

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = NameGeneratorMetadata()
        metadata.is_consistency_case_sensitive = True
        metadata.preserve_gender = True

        assert metadata.is_consistency_case_sensitive is True
        assert metadata["isConsistencyCaseSensitive"] is True
        assert metadata.preserve_gender is True
        assert metadata["preserveGender"] is True

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = NameGeneratorMetadata(is_consistency_case_sensitive=True)

        assert metadata["isConsistencyCaseSensitive"] is True
        assert metadata["_type"] == "NameGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = NameGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "NameGeneratorMetadata"
        assert payload["customGenerator"] == GeneratorType.Name

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = NameGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "DateTime"}
        with pytest.raises(Exception) as exc_info:
            NameGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
