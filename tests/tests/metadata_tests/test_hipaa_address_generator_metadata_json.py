import json
import pytest
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestHipaaAddressGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = HipaaAddressGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_non_hipaa_address_generator=True,
            replace_truncated_zeros_in_zip_code=False,
            realistic_synthetic_values=False,
            swaps={"Atlanta": "Boston"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "HipaaAddressGenerator"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["useNonHipaaAddressGenerator"] is True
        assert parsed["replaceTruncatedZerosInZipCode"] is False
        assert parsed["realisticSyntheticValues"] is False
        assert parsed["swaps"] == {"Atlanta": "Boston"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = HipaaAddressGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "HipaaAddressGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = HipaaAddressGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = HipaaAddressGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.use_non_hipaa_address_generator == original.use_non_hipaa_address_generator
        assert restored.replace_truncated_zeros_in_zip_code == original.replace_truncated_zeros_in_zip_code
        assert restored.realistic_synthetic_values == original.realistic_synthetic_values
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = HipaaAddressGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_non_hipaa_address_generator=True,
            replace_truncated_zeros_in_zip_code=False,
            realistic_synthetic_values=False,
            swaps={"city1": "city2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = HipaaAddressGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.HipaaAddressGenerator
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.use_non_hipaa_address_generator is True
        assert restored.replace_truncated_zeros_in_zip_code is False
        assert restored.realistic_synthetic_values is False
        assert restored.swaps == {"city1": "city2"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = HipaaAddressGeneratorMetadata(
            use_non_hipaa_address_generator=True,
            replace_truncated_zeros_in_zip_code=False
        )

        assert metadata.use_non_hipaa_address_generator is True
        assert metadata.replace_truncated_zeros_in_zip_code is False
        assert metadata.custom_generator == GeneratorType.HipaaAddressGenerator

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = HipaaAddressGeneratorMetadata()
        metadata.use_non_hipaa_address_generator = True
        metadata.replace_truncated_zeros_in_zip_code = False
        metadata.realistic_synthetic_values = False

        assert metadata.use_non_hipaa_address_generator is True
        assert metadata["useNonHipaaAddressGenerator"] is True
        assert metadata.replace_truncated_zeros_in_zip_code is False
        assert metadata["replaceTruncatedZerosInZipCode"] is False
        assert metadata.realistic_synthetic_values is False
        assert metadata["realisticSyntheticValues"] is False

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = HipaaAddressGeneratorMetadata(use_non_hipaa_address_generator=True)

        assert metadata["useNonHipaaAddressGenerator"] is True
        assert metadata["_type"] == "HipaaAddressGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = HipaaAddressGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "HipaaAddressGeneratorMetadata"
        assert payload["customGenerator"] == GeneratorType.HipaaAddressGenerator

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = HipaaAddressGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            HipaaAddressGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
