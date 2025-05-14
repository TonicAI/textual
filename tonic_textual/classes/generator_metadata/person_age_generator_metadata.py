from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata, default_age_shift_metadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class PersonAgeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(self, age_shift_metadata: Optional[AgeShiftMetadata] = default_age_shift_metadata):
        super().__init__()
        self._date_time_transformation = "AgeShift"
        self._metadata = age_shift_metadata

    def to_payload(self, default: "PersonAgeGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        result["dateTimeTransformation"] = self._date_time_transformation
        result["metadata"] = self._metadata.to_payload(default._metadata)

        return result


    def date_time_transformation(self) -> str:
        return "AgeShift"

    def metadata(self) -> BaseMetadata:
        return self._metadata

default_person_age_metadata = PersonAgeGeneratorMetadata()
def person_age_metadata_to_payload(metadata: PersonAgeGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_person_age_metadata)