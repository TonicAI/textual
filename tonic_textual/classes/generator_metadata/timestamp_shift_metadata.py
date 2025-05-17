from typing import Dict


class TimestampShiftMetadata:
    def __init__(
            self,
            timestamp_shift_in_days: int = 7
    ):
        self.timestamp_shift_in_days = timestamp_shift_in_days

    def to_payload(self) -> Dict:
        result = dict()
        
        result["timestampShiftInDays"] = self.timestamp_shift_in_days

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "TimestampShiftMetadata":
        result = TimestampShiftMetadata()

        result.timestamp_shift_in_days = payload.get("timestampShiftInDays", default_timestamp_shift_metadata.timestamp_shift_in_days)

        return result

default_timestamp_shift_metadata = TimestampShiftMetadata()