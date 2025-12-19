import json
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestBaseMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = BaseMetadata(
            custom_generator=GeneratorType.Name,
            generator_version=GeneratorVersion.V2,
            swaps={"foo": "bar"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "Name"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["swaps"] == {"foo": "bar"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = BaseMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "BaseMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = BaseMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = BaseMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = BaseMetadata(
            custom_generator=GeneratorType.DateTime,
            generator_version=GeneratorVersion.V2,
            swaps={"original": "replaced"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = BaseMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = BaseMetadata(
            custom_generator=GeneratorType.Name,
            generator_version=GeneratorVersion.V1,
            swaps={"a": "b"}
        )

        assert metadata.custom_generator == GeneratorType.Name
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {"a": "b"}

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = BaseMetadata()
        metadata.custom_generator = GeneratorType.Email
        metadata.generator_version = GeneratorVersion.V2
        metadata.swaps = {"x": "y"}

        assert metadata.custom_generator == GeneratorType.Email
        assert metadata["customGenerator"] == GeneratorType.Email
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata["generatorVersion"] == GeneratorVersion.V2
        assert metadata.swaps == {"x": "y"}
        assert metadata["swaps"] == {"x": "y"}

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = BaseMetadata(custom_generator=GeneratorType.Ssn)

        assert metadata["customGenerator"] == GeneratorType.Ssn
        assert metadata["_type"] == "BaseMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = BaseMetadata(custom_generator=GeneratorType.Url)
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["customGenerator"] == GeneratorType.Url
        assert payload["_type"] == "BaseMetadata"

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = BaseMetadata()

        assert isinstance(metadata, dict)

    def test_none_custom_generator_serializes_correctly(self):
        """None custom_generator should serialize to null in JSON."""
        metadata = BaseMetadata(custom_generator=None)
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["customGenerator"] is None
