from typing import Dict

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata, default_age_shift_metadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PersonAgeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            metadata: AgeShiftMetadata = default_age_shift_metadata
    ):
        super().__init__(
            custom_generator=GeneratorType.PersonAge,
            generator_version=generator_version,
            scramble_unrecognized_dates=scramble_unrecognized_dates
        )
        self.metadata = metadata

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["metadata"] = self.metadata.to_payload()

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "PersonAgeGeneratorMetadata":
        base_metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)
        result = PersonAgeGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.PersonAge:
            raise Exception(
                f"Invalid value for custom generator: "
                f"PersonAgeGeneratorMetadata requires {GeneratorType.PersonAge.value} but got {result.custom_generator}"
            )

        result.generator_version = base_metadata.generator_version
        result.scramble_unrecognized_dates = base_metadata.scramble_unrecognized_dates
        result.metadata = AgeShiftMetadata.from_payload(payload.get("metadata", dict()))

        return result

default_person_age_generator_metadata = PersonAgeGeneratorMetadata()