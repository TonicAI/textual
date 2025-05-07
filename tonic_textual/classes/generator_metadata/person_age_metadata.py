from typing import Dict

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata, default_age_shift_metadata
from tonic_textual.classes.generator_metadata.base_date_time_metadata import BaseDateTimeMetadata
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class PersonAgeMetadata(BaseDateTimeMetadata):
    _date_time_transformation: str
    _metadata: AgeShiftMetadata

    def __init__(self):
        super().__init__()
        self._date_time_transformation = "AgeShift"
        self._metadata = default_age_shift_metadata

    def __eq__(self, other: "PersonAgeMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self._date_time_transformation != other._date_time_transformation:
            return False

        if self._metadata != other._metadata:
            return False

        return True

    def to_payload(self, default: "PersonAgeMetadata") -> Dict:
        result = super().to_payload(default)

        if self._date_time_transformation != default._date_time_transformation:
            result["dateTimeTransformation"] = self._date_time_transformation

        if self._metadata != default._metadata:
            result["metadata"] = self._metadata.to_payload(default._metadata)

        return result


    def date_time_transformation(self) -> str:
        return "AgeShift"

    def metadata(self) -> BaseMetadata:
        return self._metadata

default_person_age_metadata = PersonAgeMetadata()
def person_age_metadata_to_payload(metadata: PersonAgeMetadata) -> Dict:
    return metadata.to_payload(default_person_age_metadata)