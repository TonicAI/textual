from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.string_date_format import StringDateFormat


class TimestampShiftMetadata(BaseMetadata):
    timestamp_shift_in_days: int
    date_format: StringDateFormat

    def __init__(self):
        super().__init__()
        self.timestamp_shift_in_days = 7
        self.date_format = StringDateFormat.YearMonthDayNoSeparator

    def __eq__(self, other: "TimestampShiftMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.timestamp_shift_in_days != other.timestamp_shift_in_days:
            return False

        if self.date_format != other.date_format:
            return False

        return True

    def to_payload(self, default: "TimestampShiftMetadata") -> Dict:
        result = super().to_payload(default)

        if self.timestamp_shift_in_days != default.timestamp_shift_in_days:
            result["timestampShiftInDays"] = self.timestamp_shift_in_days

        if self.date_format != default.date_format:
            result["dateFormat"] = self.date_format

        return result

default_timestamp_shift_metadata = TimestampShiftMetadata()
def timestamp_shift_metadata_to_payload(metadata: TimestampShiftMetadata) -> Dict:
    return metadata.to_payload(default_timestamp_shift_metadata)