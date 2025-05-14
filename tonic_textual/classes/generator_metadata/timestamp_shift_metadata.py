from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata

class TimestampShiftMetadata(BaseMetadata):

    def __init__(self, timestamp_shift_in_days: Optional[int] = 7):
        super().__init__()
        self.timestamp_shift_in_days = timestamp_shift_in_days

    def to_payload(self, default: "TimestampShiftMetadata") -> Dict:
        result = super().to_payload(default)
        
        result["timestampShiftInDays"] = self.timestamp_shift_in_days        
        return result

default_timestamp_shift_metadata = TimestampShiftMetadata()
def timestamp_shift_metadata_to_payload(metadata: TimestampShiftMetadata) -> Dict:
    return metadata.to_payload(default_timestamp_shift_metadata)