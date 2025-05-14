from typing import List, Dict, Optional

from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata, default_timestamp_shift_metadata


class DateTimeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(self, additional_date_formats: Optional[List[str]] = [], apply_constant_shift_to_document: Optional[bool] = False, timestamp_shift_metadata: Optional[TimestampShiftMetadata] = default_timestamp_shift_metadata):
        super().__init__()
        self._date_time_transformation = "TimestampShift"
        self._metadata = timestamp_shift_metadata
        self.additional_date_formats = additional_date_formats
        self.apply_constant_shift_to_document = apply_constant_shift_to_document

    def to_payload(self, default: "DateTimeGeneratorMetadata") -> Dict:
        result = super().to_payload(default)
        
        result["dateTimeTransformation"] = self._date_time_transformation
        result["metadata"] = self._metadata.to_payload(default._metadata)
        result["additionalDateFormats"] = self.additional_date_formats    
        result["applyConstantShiftToDocument"] = self.apply_constant_shift_to_document

        return result

    def date_time_transformation(self) -> str:
        return self._date_time_transformation

    def metadata(self) -> BaseMetadata:
        return self._metadata

default_date_time_metadata = DateTimeGeneratorMetadata()
def date_time_metadata_to_payload(metadata: DateTimeGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_date_time_metadata)
