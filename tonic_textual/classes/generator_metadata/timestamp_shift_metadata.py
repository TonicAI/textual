from typing import Dict, Optional
import warnings
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class TimestampShiftMetadata(BaseMetadata):

    def __init__(
            self,
            left_shift_in_days: Optional[int] = -7,
            right_shift_in_days: Optional[int] = 7,
            time_stamp_shift_in_days: Optional[int] = None,
            swaps: Optional[Dict[str,str]] = {}):
        super().__init__(swaps=swaps)

        if time_stamp_shift_in_days is not None:
            warnings.warn("time_stamp_shift_in_days is being deprated and will not be supported past v285 of the product.")

        self["leftShiftInDays"] = left_shift_in_days
        self["rightShiftInDays"] = right_shift_in_days
        if time_stamp_shift_in_days is not None:
            self["timestampShiftInDays"] = time_stamp_shift_in_days

    @property
    def left_shift_in_days(self) -> Optional[int]:
        return self.get("leftShiftInDays")

    @left_shift_in_days.setter
    def left_shift_in_days(self, value: Optional[int]):
        self["leftShiftInDays"] = value

    @property
    def right_shift_in_days(self) -> Optional[int]:
        return self.get("rightShiftInDays")

    @right_shift_in_days.setter
    def right_shift_in_days(self, value: Optional[int]):
        self["rightShiftInDays"] = value

    @property
    def time_stamp_shift_in_days(self) -> Optional[int]:
        return self.get("timestampShiftInDays")

    @time_stamp_shift_in_days.setter
    def time_stamp_shift_in_days(self, value: Optional[int]):
        if value is not None:
            self["timestampShiftInDays"] = value
        elif "timestampShiftInDays" in self:
            del self["timestampShiftInDays"]

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "TimestampShiftMetadata":
        swaps = payload.get("swaps", {})
        left_shift = payload.get("leftShiftInDays", -7)
        right_shift = payload.get("rightShiftInDays", 7)
        time_stamp_shift = payload.get("timestampShiftInDays", None)

        return TimestampShiftMetadata(
            left_shift_in_days=left_shift,
            right_shift_in_days=right_shift,
            time_stamp_shift_in_days=time_stamp_shift,
            swaps=swaps
        )

default_timestamp_shift_metadata = TimestampShiftMetadata()