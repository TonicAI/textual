from typing import Dict, Optional


class TimestampShiftMetadata:
    def __init__(
            self,
            timestamp_shift_in_days: Optional[int] = 7
    ):
        self.timestamp_shift_in_days = timestamp_shift_in_days

    def to_payload(self) -> Dict:
        result = dict()
        
        result["timestampShiftInDays"] = self.timestamp_shift_in_days

        return result

default_timestamp_shift_metadata = TimestampShiftMetadata()