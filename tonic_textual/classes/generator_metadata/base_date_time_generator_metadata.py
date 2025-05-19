from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseDateTimeGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            custom_generator: Optional[GeneratorType] = None,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True
    ):
        super().__init__(
            custom_generator=custom_generator,
            generator_version=generator_version
        )
        self.scramble_unrecognized_dates = scramble_unrecognized_dates

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["scrambleUnrecognizedDates"] = self.scramble_unrecognized_dates

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "BaseDateTimeGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)
        result = BaseDateTimeGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        result.generator_version = base_metadata.generator_version
        result.scramble_unrecognized_dates = payload.get("scrambleUnrecognizedDates", default_base_date_time_generator_metadata.scramble_unrecognized_dates)

        return result

default_base_date_time_generator_metadata = BaseDateTimeGeneratorMetadata()
