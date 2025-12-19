from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseDateTimeGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            custom_generator: Optional[GeneratorType] = None,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
            custom_generator=custom_generator,
            generator_version=generator_version,
            swaps=swaps
        )
        self["scrambleUnrecognizedDates"] = scramble_unrecognized_dates

    @property
    def scramble_unrecognized_dates(self) -> bool:
        return self["scrambleUnrecognizedDates"]

    @scramble_unrecognized_dates.setter
    def scramble_unrecognized_dates(self, value: bool):
        self["scrambleUnrecognizedDates"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "BaseDateTimeGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        return BaseDateTimeGeneratorMetadata(
            custom_generator=base_metadata.custom_generator,
            generator_version=base_metadata.generator_version,
            swaps=base_metadata.swaps,
            scramble_unrecognized_dates=payload.get("scrambleUnrecognizedDates", True)
        )

default_base_date_time_generator_metadata = BaseDateTimeGeneratorMetadata()
