from typing import List, Dict

from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata, default_timestamp_shift_metadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class DateTimeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            additional_date_formats: List[str] = list(),
            apply_constant_shift_to_document: bool = False,
            metadata: TimestampShiftMetadata = default_timestamp_shift_metadata
    ):
        super().__init__(
            custom_generator=GeneratorType.DateTime,
            generator_version=generator_version,
            scramble_unrecognized_dates=scramble_unrecognized_dates
        )
        self.metadata = metadata
        self.additional_date_formats = additional_date_formats
        self.apply_constant_shift_to_document = apply_constant_shift_to_document

    def to_payload(self) -> Dict:
        result = super().to_payload()
        
        result["metadata"] = self.metadata.to_payload()
        result["additionalDateFormats"] = self.additional_date_formats    
        result["applyConstantShiftToDocument"] = self.apply_constant_shift_to_document

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "DateTimeGeneratorMetadata":
        base_metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)
        result = DateTimeGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.DateTime:
            raise Exception(
                f"Invalid value for custom generator: "
                f"DateTimeGeneratorMetadata requires {GeneratorType.DateTime.value} but got {result.custom_generator.name}"
            )

        result.generator_version = base_metadata.generator_version
        result.scramble_unrecognized_dates = base_metadata.scramble_unrecognized_dates
        result.metadata = TimestampShiftMetadata.from_payload(payload.get("metadata", dict()))
        result.additional_date_formats = payload.get("additionalDateFormats",default_date_time_generator_metadata.additional_date_formats)
        result.apply_constant_shift_to_document = payload.get("applyConstantShiftToDocument",default_date_time_generator_metadata.apply_constant_shift_to_document)

        return result

default_date_time_generator_metadata = DateTimeGeneratorMetadata()
