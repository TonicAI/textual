from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class BaseDateTimeGeneratorMetadata(BaseMetadata):
    def __init__(self, scramble_unrecognized_dates: Optional[bool] = True):
        super().__init__()
        self.scramble_unrecognized_dates = scramble_unrecognized_dates

    def to_payload(self, default: "BaseDateTimeGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        if self.scramble_unrecognized_dates != default.scramble_unrecognized_dates:
            result["scrambleUnrecognizedDates"] = self.scramble_unrecognized_dates

        return result

    def date_time_transformation(self) -> str:
        raise NotImplementedError

    def metadata(self) -> BaseMetadata:
        raise NotImplementedError
