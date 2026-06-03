import json
from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata


class TestAgeShiftMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        metadata = AgeShiftMetadata(age_shift_in_years=10)
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["ageShiftInYears"] == 10

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = AgeShiftMetadata(age_shift_in_years=15)
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "AgeShiftMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = AgeShiftMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = AgeShiftMetadata.from_payload(parsed)

        assert restored.age_shift_in_years == original.age_shift_in_years
        assert restored.apply_constant_shift_to_document == original.apply_constant_shift_to_document

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = AgeShiftMetadata(age_shift_in_years=42, apply_constant_shift_to_document=True)
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = AgeShiftMetadata.from_payload(parsed)

        assert restored.age_shift_in_years == 42
        assert restored.apply_constant_shift_to_document is True

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = AgeShiftMetadata(age_shift_in_years=20, apply_constant_shift_to_document=True)

        assert metadata.age_shift_in_years == 20
        assert metadata.apply_constant_shift_to_document is True

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = AgeShiftMetadata(age_shift_in_years=10)
        metadata.age_shift_in_years = 25
        metadata.apply_constant_shift_to_document = True

        assert metadata.age_shift_in_years == 25
        assert metadata["ageShiftInYears"] == 25
        assert metadata.apply_constant_shift_to_document is True
        assert metadata["applyConstantShiftToDocument"] is True

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = AgeShiftMetadata(age_shift_in_years=30)

        assert metadata["ageShiftInYears"] == 30
        assert metadata["_type"] == "AgeShiftMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = AgeShiftMetadata(age_shift_in_years=50, apply_constant_shift_to_document=True)
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["ageShiftInYears"] == 50
        assert payload["applyConstantShiftToDocument"] is True
        assert payload["_type"] == "AgeShiftMetadata"

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = AgeShiftMetadata()

        assert isinstance(metadata, dict)

    def test_apply_constant_shift_to_document_defaults_to_false(self):
        """Default for apply_constant_shift_to_document should be False."""
        metadata = AgeShiftMetadata()

        assert metadata.apply_constant_shift_to_document is False
        assert metadata["applyConstantShiftToDocument"] is False

    def test_from_payload_omits_apply_constant_shift_defaults_to_false(self):
        """Older payloads without applyConstantShiftToDocument should default to False
        so the SDK stays backward-compatible with servers/JSON that pre-date the field."""
        legacy_payload = {"ageShiftInYears": 12}
        restored = AgeShiftMetadata.from_payload(legacy_payload)

        assert restored.age_shift_in_years == 12
        assert restored.apply_constant_shift_to_document is False
