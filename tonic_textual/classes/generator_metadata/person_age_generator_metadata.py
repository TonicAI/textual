from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata, default_age_shift_metadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PersonAgeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            metadata: AgeShiftMetadata = None,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
            custom_generator=GeneratorType.PersonAge,
            generator_version=generator_version,
            scramble_unrecognized_dates=scramble_unrecognized_dates,
            swaps=swaps
        )
        if metadata is None:
            metadata = AgeShiftMetadata()
        self["metadata"] = metadata

    @property
    def metadata(self) -> AgeShiftMetadata:
        return self["metadata"]

    @metadata.setter
    def metadata(self, value: AgeShiftMetadata):
        self["metadata"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "PersonAgeGeneratorMetadata":
        base_metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.PersonAge:
            raise Exception(
                f"Invalid value for custom generator: "
                f"PersonAgeGeneratorMetadata requires {GeneratorType.PersonAge.value} but got {base_metadata.custom_generator}"
            )

        metadata_payload = payload.get("metadata", {})
        age_metadata = AgeShiftMetadata.from_payload(metadata_payload)

        return PersonAgeGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            scramble_unrecognized_dates=base_metadata.scramble_unrecognized_dates,
            metadata=age_metadata,
            swaps=base_metadata.swaps
        )

default_person_age_generator_metadata = PersonAgeGeneratorMetadata()