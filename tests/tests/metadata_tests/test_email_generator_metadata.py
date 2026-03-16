import json
import pytest
from tonic_textual.classes.generator_metadata.email_generator_metadata import EmailGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestEmailGeneratorMetadataPayload:
    def test_to_payload_defaults(self):
        metadata = EmailGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.Email
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["preserveDomain"] is False

    def test_to_payload_with_values(self):
        metadata = EmailGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            preserve_domain=True,
            swaps={"user@old.com": "user@new.com"}
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.Email
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"user@old.com": "user@new.com"}
        assert payload["preserveDomain"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "Email"}
        metadata = EmailGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.Email
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.preserve_domain is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "Email",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"a@b.com": "c@d.com"},
            "preserveDomain": True
        }
        metadata = EmailGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.Email
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"a@b.com": "c@d.com"}
        assert metadata.preserve_domain is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            EmailGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        original = EmailGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            preserve_domain=True,
            swaps={"email1": "email2"}
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = EmailGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.preserve_domain == original.preserve_domain


class TestEmailGeneratorMetadataJson:
    def test_json_dumps_works_directly(self):
        metadata = EmailGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            preserve_domain=True,
            swaps={"user@old.com": "user@new.com"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "Email"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["preserveDomain"] is True
        assert parsed["swaps"] == {"user@old.com": "user@new.com"}

    def test_json_includes_type_field(self):
        metadata = EmailGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "EmailGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        original = EmailGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = EmailGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.preserve_domain == original.preserve_domain
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        original = EmailGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            preserve_domain=True,
            swaps={"email1": "email2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = EmailGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.Email
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.preserve_domain is True
        assert restored.swaps == {"email1": "email2"}

    def test_attribute_access_works(self):
        metadata = EmailGeneratorMetadata(preserve_domain=True)

        assert metadata.preserve_domain is True
        assert metadata.custom_generator == GeneratorType.Email

    def test_attribute_setter_works(self):
        metadata = EmailGeneratorMetadata()
        metadata.preserve_domain = True

        assert metadata.preserve_domain is True
        assert metadata["preserveDomain"] is True

    def test_dict_access_works(self):
        metadata = EmailGeneratorMetadata(preserve_domain=True)

        assert metadata["preserveDomain"] is True
        assert metadata["_type"] == "EmailGeneratorMetadata"

    def test_is_instance_of_dict(self):
        metadata = EmailGeneratorMetadata()

        assert isinstance(metadata, dict)
