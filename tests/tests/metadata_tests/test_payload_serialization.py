import pytest
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class TestBaseMetadata:
    def test_to_payload_defaults(self):
        metadata = BaseMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] is None
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["constantValue"] is None

    def test_to_payload_with_values(self):
        metadata = BaseMetadata(
            custom_generator=GeneratorType.Name,
            generator_version=GeneratorVersion.V2,
            swaps={"foo": "bar"},
            constant_value="REDACTED"
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.Name
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"foo": "bar"}
        assert payload["constantValue"] == "REDACTED"

    def test_from_payload_empty(self):
        metadata = BaseMetadata.from_payload({})

        assert metadata.custom_generator is None
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.constant_value is None

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "Name",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"key": "value"},
            "constantValue": "STATIC"
        }
        metadata = BaseMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.Name
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"key": "value"}
        assert metadata.constant_value == "STATIC"

    def test_roundtrip(self):
        original = BaseMetadata(
            custom_generator=GeneratorType.DateTime,
            generator_version=GeneratorVersion.V2,
            swaps={"original": "replaced"},
            constant_value="FIXED"
        )
        payload = original.to_payload()
        # Convert enum to string as would happen in JSON serialization
        payload["customGenerator"] = payload["customGenerator"].value
        restored = BaseMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.constant_value == original.constant_value


class TestNameGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = NameGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.Name
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["isConsistencyCaseSensitive"] is False
        assert payload["preserveGender"] is False

    def test_to_payload_with_values(self):
        metadata = NameGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            is_consistency_case_sensitive=True,
            preserve_gender=True,
            swaps={"John": "Jane"}
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.Name
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"John": "Jane"}
        assert payload["isConsistencyCaseSensitive"] is True
        assert payload["preserveGender"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "Name"}
        metadata = NameGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.Name
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.is_consistency_case_sensitive is False
        assert metadata.preserve_gender is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "Name",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"Alice": "Bob"},
            "isConsistencyCaseSensitive": True,
            "preserveGender": True
        }
        metadata = NameGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.Name
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"Alice": "Bob"}
        assert metadata.is_consistency_case_sensitive is True
        assert metadata.preserve_gender is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "DateTime"}
        with pytest.raises(Exception) as exc_info:
            NameGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        original = NameGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            is_consistency_case_sensitive=True,
            preserve_gender=True,
            swaps={"name1": "name2"}
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = NameGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.is_consistency_case_sensitive == original.is_consistency_case_sensitive
        assert restored.preserve_gender == original.preserve_gender


class TestHipaaAddressGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = HipaaAddressGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.HipaaAddressGenerator
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["useNonHipaaAddressGenerator"] is False
        assert payload["replaceTruncatedZerosInZipCode"] is True
        assert payload["realisticSyntheticValues"] is True
        assert payload["useThreeDigitZips"] is False
        assert payload["replaceForeignZipCodesWithZeros"] is False

    def test_to_payload_with_values(self):
        metadata = HipaaAddressGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_non_hipaa_address_generator=True,
            replace_truncated_zeros_in_zip_code=False,
            realistic_synthetic_values=False,
            swaps={"Atlanta": "Boston"},
            use_three_digit_zips=True,
            replace_foreign_zip_codes_with_zeros=True
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.HipaaAddressGenerator
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"Atlanta": "Boston"}
        assert payload["useNonHipaaAddressGenerator"] is True
        assert payload["replaceTruncatedZerosInZipCode"] is False
        assert payload["realisticSyntheticValues"] is False
        assert payload["useThreeDigitZips"] is True
        assert payload["replaceForeignZipCodesWithZeros"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "HipaaAddressGenerator"}
        metadata = HipaaAddressGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.HipaaAddressGenerator
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.use_non_hipaa_address_generator is False
        assert metadata.replace_truncated_zeros_in_zip_code is True
        assert metadata.realistic_synthetic_values is True
        assert metadata.use_three_digit_zips is False
        assert metadata.replace_foreign_zip_codes_with_zeros is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "HipaaAddressGenerator",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"NY": "CA"},
            "useNonHipaaAddressGenerator": True,
            "replaceTruncatedZerosInZipCode": False,
            "realisticSyntheticValues": False,
            "useThreeDigitZips": True,
            "replaceForeignZipCodesWithZeros": True
        }
        metadata = HipaaAddressGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.HipaaAddressGenerator
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"NY": "CA"}
        assert metadata.use_non_hipaa_address_generator is True
        assert metadata.replace_truncated_zeros_in_zip_code is False
        assert metadata.realistic_synthetic_values is False
        assert metadata.use_three_digit_zips is True
        assert metadata.replace_foreign_zip_codes_with_zeros is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            HipaaAddressGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        original = HipaaAddressGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_non_hipaa_address_generator=True,
            replace_truncated_zeros_in_zip_code=False,
            realistic_synthetic_values=False,
            swaps={"city1": "city2"},
            use_three_digit_zips=True,
            replace_foreign_zip_codes_with_zeros=True
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = HipaaAddressGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.use_non_hipaa_address_generator == original.use_non_hipaa_address_generator
        assert restored.replace_truncated_zeros_in_zip_code == original.replace_truncated_zeros_in_zip_code
        assert restored.realistic_synthetic_values == original.realistic_synthetic_values
        assert restored.use_three_digit_zips == original.use_three_digit_zips
        assert restored.replace_foreign_zip_codes_with_zeros == original.replace_foreign_zip_codes_with_zeros


class TestNumericValueGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = NumericValueGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.NumericValue
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["useOracleIntegerPkGenerator"] is False

    def test_to_payload_with_values(self):
        metadata = NumericValueGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_oracle_integer_pk_generator=True,
            swaps={"123": "456"}
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.NumericValue
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"123": "456"}
        assert payload["useOracleIntegerPkGenerator"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "NumericValue"}
        metadata = NumericValueGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.NumericValue
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.use_oracle_integer_pk_generator is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "NumericValue",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"100": "200"},
            "useOracleIntegerPkGenerator": True
        }
        metadata = NumericValueGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.NumericValue
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"100": "200"}
        assert metadata.use_oracle_integer_pk_generator is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            NumericValueGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        original = NumericValueGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_oracle_integer_pk_generator=True,
            swaps={"val1": "val2"}
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = NumericValueGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.use_oracle_integer_pk_generator == original.use_oracle_integer_pk_generator


class TestPhoneNumberGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = PhoneNumberGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.PhoneNumber
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["useUsPhoneNumberGenerator"] is False
        assert payload["replaceInvalidNumbers"] is True

    def test_to_payload_with_values(self):
        metadata = PhoneNumberGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_us_phone_number_generator=True,
            replace_invalid_numbers=False,
            swaps={"555-1234": "555-5678"}
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.PhoneNumber
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"555-1234": "555-5678"}
        assert payload["useUsPhoneNumberGenerator"] is True
        assert payload["replaceInvalidNumbers"] is False

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "PhoneNumber"}
        metadata = PhoneNumberGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.PhoneNumber
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.use_us_phone_number_generator is False
        assert metadata.replace_invalid_numbers is True

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "PhoneNumber",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"111": "222"},
            "useUsPhoneNumberGenerator": True,
            "replaceInvalidNumbers": False
        }
        metadata = PhoneNumberGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.PhoneNumber
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"111": "222"}
        assert metadata.use_us_phone_number_generator is True
        assert metadata.replace_invalid_numbers is False

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            PhoneNumberGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        original = PhoneNumberGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            use_us_phone_number_generator=True,
            replace_invalid_numbers=False,
            swaps={"phone1": "phone2"}
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = PhoneNumberGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.use_us_phone_number_generator == original.use_us_phone_number_generator
        assert restored.replace_invalid_numbers == original.replace_invalid_numbers


class TestBaseDateTimeGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = BaseDateTimeGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] is None
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["scrambleUnrecognizedDates"] is True

    def test_to_payload_with_values(self):
        metadata = BaseDateTimeGeneratorMetadata(
            custom_generator=GeneratorType.DateTime,
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            swaps={"2024-01-01": "2025-01-01"}
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.DateTime
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"2024-01-01": "2025-01-01"}
        assert payload["scrambleUnrecognizedDates"] is False

    def test_from_payload_defaults(self):
        metadata = BaseDateTimeGeneratorMetadata.from_payload({})

        assert metadata.custom_generator is None
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.scramble_unrecognized_dates is True

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "DateTime",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"date1": "date2"},
            "scrambleUnrecognizedDates": False
        }
        metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.DateTime
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"date1": "date2"}
        assert metadata.scramble_unrecognized_dates is False

    def test_roundtrip(self):
        original = BaseDateTimeGeneratorMetadata(
            custom_generator=GeneratorType.PersonAge,
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            swaps={"a": "b"}
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = BaseDateTimeGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates


class TestDateTimeGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = DateTimeGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.DateTime
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["scrambleUnrecognizedDates"] is True
        assert payload["additionalDateFormats"] == []
        assert payload["applyConstantShiftToDocument"] is False
        assert "metadata" in payload
        assert payload["metadata"]["leftShiftInDays"] == -7
        assert payload["metadata"]["rightShiftInDays"] == 7
        assert payload["useClearDateAndPassthroughOrGroupYearGenerator"] is False

    def test_to_payload_with_values(self):
        ts_metadata = TimestampShiftMetadata(
            left_shift_in_days=-30,
            right_shift_in_days=30,
            swaps={"ts1": "ts2"}
        )
        metadata = DateTimeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            additional_date_formats=["yyyy-MM-dd", "dd/MM/yyyy"],
            apply_constant_shift_to_document=True,
            metadata=ts_metadata,
            swaps={"date": "newdate"},
            use_clear_date_and_passthrough_or_group_year_generator=True
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.DateTime
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"date": "newdate"}
        assert payload["scrambleUnrecognizedDates"] is False
        assert payload["additionalDateFormats"] == ["yyyy-MM-dd", "dd/MM/yyyy"]
        assert payload["applyConstantShiftToDocument"] is True
        assert payload["metadata"]["leftShiftInDays"] == -30
        assert payload["metadata"]["rightShiftInDays"] == 30
        assert payload["metadata"]["swaps"] == {"ts1": "ts2"}
        assert payload["useClearDateAndPassthroughOrGroupYearGenerator"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "DateTime"}
        metadata = DateTimeGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.DateTime
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.scramble_unrecognized_dates is True
        assert metadata.additional_date_formats == []
        assert metadata.apply_constant_shift_to_document is False
        assert metadata.metadata.left_shift_in_days == -7
        assert metadata.metadata.right_shift_in_days == 7
        assert metadata.use_clear_date_and_passthrough_or_group_year_generator is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "DateTime",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"k": "v"},
            "scrambleUnrecognizedDates": False,
            "additionalDateFormats": ["MM-dd-yyyy"],
            "applyConstantShiftToDocument": True,
            "metadata": {
                "leftShiftInDays": -100,
                "rightShiftInDays": 100,
                "swaps": {"inner": "swap"}
            },
            "useClearDateAndPassthroughOrGroupYearGenerator": True
        }
        metadata = DateTimeGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.DateTime
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"k": "v"}
        assert metadata.scramble_unrecognized_dates is False
        assert metadata.additional_date_formats == ["MM-dd-yyyy"]
        assert metadata.apply_constant_shift_to_document is True
        assert metadata.metadata.left_shift_in_days == -100
        assert metadata.metadata.right_shift_in_days == 100
        assert metadata.metadata.swaps == {"inner": "swap"}
        assert metadata.use_clear_date_and_passthrough_or_group_year_generator is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "Name"}
        with pytest.raises(Exception) as exc_info:
            DateTimeGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        ts_metadata = TimestampShiftMetadata(
            left_shift_in_days=-50,
            right_shift_in_days=50,
            swaps={"ts": "swap"}
        )
        original = DateTimeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            additional_date_formats=["format1", "format2"],
            apply_constant_shift_to_document=True,
            metadata=ts_metadata,
            swaps={"outer": "swap"},
            use_clear_date_and_passthrough_or_group_year_generator=True
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = DateTimeGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.additional_date_formats == original.additional_date_formats
        assert restored.apply_constant_shift_to_document == original.apply_constant_shift_to_document
        assert restored.metadata.left_shift_in_days == original.metadata.left_shift_in_days
        assert restored.metadata.right_shift_in_days == original.metadata.right_shift_in_days
        assert restored.metadata.swaps == original.metadata.swaps
        assert restored.use_clear_date_and_passthrough_or_group_year_generator == original.use_clear_date_and_passthrough_or_group_year_generator


class TestPersonAgeGeneratorMetadata:
    def test_to_payload_defaults(self):
        metadata = PersonAgeGeneratorMetadata()
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.PersonAge
        assert payload["generatorVersion"] == GeneratorVersion.V1
        assert payload["swaps"] == {}
        assert payload["scrambleUnrecognizedDates"] is True
        assert "metadata" in payload
        assert payload["metadata"]["ageShiftInYears"] == 7
        assert payload["usePassthroughOrGroupAgeGenerator"] is False

    def test_to_payload_with_values(self):
        age_metadata = AgeShiftMetadata(age_shift_in_years=15)
        metadata = PersonAgeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            metadata=age_metadata,
            swaps={"30": "35"},
            use_passthrough_or_group_age_generator=True
        )
        payload = metadata.to_payload()

        assert payload["customGenerator"] == GeneratorType.PersonAge
        assert payload["generatorVersion"] == GeneratorVersion.V2
        assert payload["swaps"] == {"30": "35"}
        assert payload["scrambleUnrecognizedDates"] is False
        assert payload["metadata"]["ageShiftInYears"] == 15
        assert payload["usePassthroughOrGroupAgeGenerator"] is True

    def test_from_payload_defaults(self):
        payload = {"customGenerator": "PersonAge"}
        metadata = PersonAgeGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.PersonAge
        assert metadata.generator_version == GeneratorVersion.V1
        assert metadata.swaps == {}
        assert metadata.scramble_unrecognized_dates is True
        assert metadata.metadata.age_shift_in_years == 7
        assert metadata.use_passthrough_or_group_age_generator is False

    def test_from_payload_with_values(self):
        payload = {
            "customGenerator": "PersonAge",
            "generatorVersion": GeneratorVersion.V2,
            "swaps": {"age1": "age2"},
            "scrambleUnrecognizedDates": False,
            "metadata": {
                "ageShiftInYears": 25
            },
            "usePassthroughOrGroupAgeGenerator": True
        }
        metadata = PersonAgeGeneratorMetadata.from_payload(payload)

        assert metadata.custom_generator == GeneratorType.PersonAge
        assert metadata.generator_version == GeneratorVersion.V2
        assert metadata.swaps == {"age1": "age2"}
        assert metadata.scramble_unrecognized_dates is False
        assert metadata.metadata.age_shift_in_years == 25
        assert metadata.use_passthrough_or_group_age_generator is True

    def test_from_payload_invalid_generator_raises(self):
        payload = {"customGenerator": "DateTime"}
        with pytest.raises(Exception) as exc_info:
            PersonAgeGeneratorMetadata.from_payload(payload)
        assert "Invalid value for custom generator" in str(exc_info.value)

    def test_roundtrip(self):
        age_metadata = AgeShiftMetadata(age_shift_in_years=20)
        original = PersonAgeGeneratorMetadata(
            generator_version=GeneratorVersion.V2,
            scramble_unrecognized_dates=False,
            metadata=age_metadata,
            swaps={"swap1": "swap2"},
            use_passthrough_or_group_age_generator=True
        )
        payload = original.to_payload()
        payload["customGenerator"] = payload["customGenerator"].value
        restored = PersonAgeGeneratorMetadata.from_payload(payload)

        assert restored.custom_generator == original.custom_generator
        assert restored.generator_version == original.generator_version
        assert restored.swaps == original.swaps
        assert restored.scramble_unrecognized_dates == original.scramble_unrecognized_dates
        assert restored.metadata.age_shift_in_years == original.metadata.age_shift_in_years
        assert restored.use_passthrough_or_group_age_generator == original.use_passthrough_or_group_age_generator


class TestTimestampShiftMetadata:
    def test_to_payload_defaults(self):
        metadata = TimestampShiftMetadata()
        payload = metadata.to_payload()

        assert payload["swaps"] == {}
        assert payload["leftShiftInDays"] == -7
        assert payload["rightShiftInDays"] == 7
        assert "timestampShiftInDays" not in payload

    def test_to_payload_with_values(self):
        metadata = TimestampShiftMetadata(
            left_shift_in_days=-100,
            right_shift_in_days=100,
            swaps={"ts_key": "ts_val"}
        )
        payload = metadata.to_payload()

        assert payload["swaps"] == {"ts_key": "ts_val"}
        assert payload["leftShiftInDays"] == -100
        assert payload["rightShiftInDays"] == 100

    def test_to_payload_with_deprecated_timestamp_shift(self):
        with pytest.warns(UserWarning, match="time_stamp_shift_in_days"):
            metadata = TimestampShiftMetadata(
                time_stamp_shift_in_days=50
            )
        payload = metadata.to_payload()

        assert payload["timestampShiftInDays"] == 50

    def test_from_payload_defaults(self):
        metadata = TimestampShiftMetadata.from_payload({})

        assert metadata.swaps == {}
        assert metadata.left_shift_in_days == -7
        assert metadata.right_shift_in_days == 7
        assert metadata.time_stamp_shift_in_days is None

    def test_from_payload_with_values(self):
        payload = {
            "swaps": {"key": "val"},
            "leftShiftInDays": -200,
            "rightShiftInDays": 200,
            "timestampShiftInDays": 75
        }
        metadata = TimestampShiftMetadata.from_payload(payload)

        assert metadata.swaps == {"key": "val"}
        assert metadata.left_shift_in_days == -200
        assert metadata.right_shift_in_days == 200
        assert metadata.time_stamp_shift_in_days == 75

    def test_roundtrip(self):
        original = TimestampShiftMetadata(
            left_shift_in_days=-30,
            right_shift_in_days=60,
            swaps={"swap_a": "swap_b"}
        )
        payload = original.to_payload()
        restored = TimestampShiftMetadata.from_payload(payload)

        assert restored.swaps == original.swaps
        assert restored.left_shift_in_days == original.left_shift_in_days
        assert restored.right_shift_in_days == original.right_shift_in_days


class TestAgeShiftMetadata:
    def test_to_payload_defaults(self):
        metadata = AgeShiftMetadata()
        payload = metadata.to_payload()

        assert payload["ageShiftInYears"] == 7

    def test_to_payload_with_values(self):
        metadata = AgeShiftMetadata(age_shift_in_years=100)
        payload = metadata.to_payload()

        assert payload["ageShiftInYears"] == 100

    def test_from_payload_defaults(self):
        metadata = AgeShiftMetadata.from_payload({})

        assert metadata.age_shift_in_years == 7

    def test_from_payload_with_values(self):
        payload = {"ageShiftInYears": 50}
        metadata = AgeShiftMetadata.from_payload(payload)

        assert metadata.age_shift_in_years == 50

    def test_roundtrip(self):
        original = AgeShiftMetadata(age_shift_in_years=33)
        payload = original.to_payload()
        restored = AgeShiftMetadata.from_payload(payload)

        assert restored.age_shift_in_years == original.age_shift_in_years
