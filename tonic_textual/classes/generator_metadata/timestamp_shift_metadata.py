from typing import Dict, Optional
import warnings
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata

class TimestampShiftMetadata(BaseMetadata):

    def __init__(self, left_shift_in_days: Optional[int] = -7, right_shift_in_days: Optional[int] = 7, time_stamp_shift_in_days: Optional[int] = None):
        super().__init__()

        if time_stamp_shift_in_days is not None:
            warnings.warn("time_stamp_shift_in_days is being deprated and will not be supported past v285 of the product.")

        self.left_shift_in_days = left_shift_in_days
        self.right_shift_in_days = right_shift_in_days
        self.time_stamp_shift_in_days = time_stamp_shift_in_days

    def to_payload(self) -> Dict:
        result = dict()
        
        result["leftShiftInDays"] = self.left_shift_in_days
        result["rightShiftInDays"] = self.right_shift_in_days
        if self.time_stamp_shift_in_days is not None:
            result["timestampShiftInDays"] = self.time_stamp_shift_in_days

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "TimestampShiftMetadata":
        result = TimestampShiftMetadata()

        result.time_stamp_shift_in_days = payload.get("timestampShiftInDays", default_timestamp_shift_metadata.time_stamp_shift_in_days)
        result.left_shift_in_days = payload.get("leftShiftInDays", default_timestamp_shift_metadata.left_shift_in_days)
        result.right_shift_in_days = payload.get("rightShiftInDays", default_timestamp_shift_metadata.right_shift_in_days)

        return result

default_timestamp_shift_metadata = TimestampShiftMetadata()