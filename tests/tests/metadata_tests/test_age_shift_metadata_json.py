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

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        original = AgeShiftMetadata(age_shift_in_years=42)
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = AgeShiftMetadata.from_payload(parsed)

        assert restored.age_shift_in_years == 42

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        metadata = AgeShiftMetadata(age_shift_in_years=20)

        assert metadata.age_shift_in_years == 20

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = AgeShiftMetadata(age_shift_in_years=10)
        metadata.age_shift_in_years = 25

        assert metadata.age_shift_in_years == 25
        assert metadata["ageShiftInYears"] == 25

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = AgeShiftMetadata(age_shift_in_years=30)

        assert metadata["ageShiftInYears"] == 30
        assert metadata["_type"] == "AgeShiftMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = AgeShiftMetadata(age_shift_in_years=50)
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["ageShiftInYears"] == 50
        assert payload["_type"] == "AgeShiftMetadata"

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = AgeShiftMetadata()

        assert isinstance(metadata, dict)
