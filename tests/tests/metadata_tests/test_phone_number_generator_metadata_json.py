import json
import pytest
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestPhoneNumberGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = PhoneNumberGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_us_phone_number_generator=True,
            replace_invalid_numbers=False,
            swaps={"555-1234": "555-5678"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "PhoneNumber"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["useUsPhoneNumberGenerator"] is True
        assert parsed["replaceInvalidNumbers"] is False
        assert parsed["swaps"] == {"555-1234": "555-5678"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = PhoneNumberGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "PhoneNumberGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = PhoneNumberGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = PhoneNumberGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.use_us_phone_number_generator == original.use_us_phone_number_generator
        assert restored.replace_invalid_numbers == original.replace_invalid_numbers
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = PhoneNumberGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_us_phone_number_generator=True,
            replace_invalid_numbers=False,
            swaps={"phone1": "phone2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = PhoneNumberGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.PhoneNumber
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.use_us_phone_number_generator is True
        assert restored.replace_invalid_numbers is False
        assert restored.swaps == {"phone1": "phone2"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = PhoneNumberGeneratorMetadata(
            use_us_phone_number_generator=True,
            replace_invalid_numbers=False
        )

        assert metadata.use_us_phone_number_generator is True
        assert metadata.replace_invalid_numbers is False
        assert metadata.custom_generator == GeneratorType.PhoneNumber

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = PhoneNumberGeneratorMetadata()
        metadata.use_us_phone_number_generator = True
        metadata.replace_invalid_numbers = False

        assert metadata.use_us_phone_number_generator is True
        assert metadata["useUsPhoneNumberGenerator"] is True
        assert metadata.replace_invalid_numbers is False
        assert metadata["replaceInvalidNumbers"] is False

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = PhoneNumberGeneratorMetadata(use_us_phone_number_generator=True)

        assert metadata["useUsPhoneNumberGenerator"] is True
        assert metadata["_type"] == "PhoneNumberGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = PhoneNumberGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "PhoneNumberGeneratorMetadata"
        assert payload["customGenerator"] == GeneratorType.PhoneNumber

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = PhoneNumberGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            PhoneNumberGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
