from typing import List, Dict, Optional

from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata, default_timestamp_shift_metadata


class DateTimeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(
            self,
            additional_date_formats: List[str] = list(),
            apply_constant_shift_to_document: Optional[bool] = False,
            timestamp_shift_metadata: Optional[TimestampShiftMetadata] = default_timestamp_shift_metadata
    ):
        super().__init__()
        self.metadata = timestamp_shift_metadata
        self.additional_date_formats = additional_date_formats
        self.apply_constant_shift_to_document = apply_constant_shift_to_document

    def to_payload(self) -> Dict:
        result = super().to_payload()
        
        result["metadata"] = self.metadata.to_payload()
        result["additionalDateFormats"] = self.additional_date_formats    
        result["applyConstantShiftToDocument"] = self.apply_constant_shift_to_document

        return result

default_date_time_generator_metadata = DateTimeGeneratorMetadata()
