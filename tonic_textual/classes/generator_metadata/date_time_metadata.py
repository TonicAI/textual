from typing import List, Dict

from tonic_textual.classes.generator_metadata.base_date_time_metadata import BaseDateTimeMetadata
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata, \
    default_timestamp_shift_metadata


class DateTimeMetadata(BaseDateTimeMetadata):
    _date_time_transformation: str
    _metadata: TimestampShiftMetadata
    additional_date_time_formats: List[str]
    apply_constant_shift_to_document: bool

    def __init__(self):
        super().__init__()
        self._date_time_transformation = "TimestampShift"
        self._metadata = default_timestamp_shift_metadata
        self.additional_date_time_formats = []
        self.apply_constant_shift_to_document = False

    def __eq__(self, other: "DateTimeMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self._date_time_transformation != other._date_time_transformation:
            return False

        if self._metadata != other._metadata:
            return False

        if self.additional_date_time_formats != other.additional_date_time_formats:
            return False

        if self.apply_constant_shift_to_document != other.apply_constant_shift_to_document:
            return False

        return True

    def to_payload(self, default: "DateTimeMetadata") -> Dict:
        result = super().to_payload(default)

        if self._date_time_transformation != default._date_time_transformation:
            result["dateTimeTransformation"] = self._date_time_transformation

        if self._metadata != default._metadata:
            result["metadata"] = self._metadata.to_payload(default._metadata)

        if self.additional_date_time_formats != default.additional_date_time_formats:
            result["additionalDateTimeFormats"] = self.additional_date_time_formats

        if self.apply_constant_shift_to_document != default.apply_constant_shift_to_document:
            result["applyConstantShiftToDocument"] = self.apply_constant_shift_to_document

        return result

    def date_time_transformation(self) -> str:
        return self._date_time_transformation

    def metadata(self) -> BaseMetadata:
        return self._metadata

default_date_time_metadata = DateTimeMetadata()
def date_time_metadata_to_payload(metadata: DateTimeMetadata) -> Dict:
    return metadata.to_payload(default_date_time_metadata)
