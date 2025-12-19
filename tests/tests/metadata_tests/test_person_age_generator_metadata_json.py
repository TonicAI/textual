import json
import pytest
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestPersonAgeGeneratorMetadataJsonSerialization:
    def test_json_dumps_works_directly(self):
        """json.dumps(metadata) should work without a custom encoder."""
        age_metadata = AgeShiftMetadata(age_shift_in_years=15)
        metadata = PersonAgeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            metadata=age_metadata,
            swaps={"30": "35"}
        )
        json_str = json.dumps(metadata)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["customGenerator"] == "PersonAge"
        assert parsed["generatorVersion"] == "V2"
        assert parsed["scrambleUnrecognizedDates"] is False
        assert parsed["metadata"]["ageShiftInYears"] == 15
        assert parsed["swaps"] == {"30": "35"}

    def test_json_includes_type_field(self):
        """Serialized JSON should include _type for deserialization."""
        metadata = PersonAgeGeneratorMetadata()
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["_type"] == "PersonAgeGeneratorMetadata"

    def test_json_roundtrip_with_defaults(self):
        """Round-trip serialization preserves default values."""
        original = PersonAgeGeneratorMetadata()
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = PersonAgeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.metadata.age_shift_in_years == original.metadata.age_shift_in_years
        assert restored.swaps == original.swaps

    def test_json_roundtrip_with_custom_values(self):
        """Round-trip serialization preserves custom values."""
        age_metadata = AgeShiftMetadata(age_shift_in_years=25)
        original = PersonAgeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            metadata=age_metadata,
            swaps={"age1": "age2"}
        )
        json_str = json.dumps(original)
        parsed = json.loads(json_str)
        restored = PersonAgeGeneratorMetadata.from_payload(parsed)

        assert restored.custom_generator == GeneratorType.PersonAge
        assert restored.generator_version == GeneratorVersion.V2
        assert restored.scramble_unrecognized_dates is False
        assert restored.metadata.age_shift_in_years == 25
        assert restored.swaps == {"age1": "age2"}

    def test_attribute_access_works(self):
        """Property-based attribute access should work."""
        age_metadata = AgeShiftMetadata(age_shift_in_years=20)
        metadata = PersonAgeGeneratorMetadata(metadata=age_metadata)

        assert metadata.metadata.age_shift_in_years == 20
        assert metadata.custom_generator == GeneratorType.PersonAge

    def test_attribute_setter_works(self):
        """Property setter should update the underlying dict."""
        metadata = PersonAgeGeneratorMetadata()
        new_age_metadata = AgeShiftMetadata(age_shift_in_years=50)
        metadata.metadata = new_age_metadata

        assert metadata.metadata.age_shift_in_years == 50
        assert metadata["metadata"]["ageShiftInYears"] == 50

    def test_dict_access_works(self):
        """Direct dict access should work."""
        metadata = PersonAgeGeneratorMetadata()

        assert metadata["customGenerator"] == GeneratorType.PersonAge
        assert metadata["_type"] == "PersonAgeGeneratorMetadata"

    def test_to_payload_returns_dict_copy(self):
        """to_payload() should return a dict copy of the metadata."""
        metadata = PersonAgeGeneratorMetadata()
        payload = metadata.to_payload()

        assert isinstance(payload, dict)
        assert payload["_type"] == "PersonAgeGeneratorMetadata"
        assert "metadata" in payload

    def test_is_instance_of_dict(self):
        """Metadata should be an instance of dict."""
        metadata = PersonAgeGeneratorMetadata()

        assert isinstance(metadata, dict)

    def test_nested_metadata_is_serializable(self):
        """Nested AgeShiftMetadata should serialize correctly."""
        age_metadata = AgeShiftMetadata(age_shift_in_years=100)
        metadata = PersonAgeGeneratorMetadata(metadata=age_metadata)
        json_str = json.dumps(metadata)
        parsed = json.loads(json_str)

        assert parsed["metadata"]["ageShiftInYears"] == 100
        assert parsed["metadata"]["_type"] == "AgeShiftMetadata"

    def test_from_payload_invalid_generator_raises(self):
        """from_payload should raise for invalid generator type."""
        payload = {"customGenerator": "DateTime"}
        with pytest.raises(Exception) as exc_info:
            PersonAgeGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)
