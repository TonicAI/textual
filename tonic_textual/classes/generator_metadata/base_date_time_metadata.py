from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata, base_metadata_to_payload


class BaseDateTimeMetadata(BaseMetadata):
    scramble_unrecognized_dates: bool

    def __init__(self):
        super().__init__()
        self.scramble_unrecognized_dates = True

    def __eq__(self, other: "BaseDateTimeMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.scramble_unrecognized_dates != other.scramble_unrecognized_dates:
            return False

        return True

    def to_payload(self, default: "BaseDateTimeMetadata") -> Dict:
        result = super().to_payload(default)

        if self.scramble_unrecognized_dates != default.scramble_unrecognized_dates:
            result["scrambleUnrecognizedDates"] = self.scramble_unrecognized_dates

        return result

    def date_time_transformation(self) -> str:
        raise NotImplementedError

    def metadata(self) -> BaseMetadata:
        raise NotImplementedError
