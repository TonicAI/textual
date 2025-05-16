from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata, default_age_shift_metadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata


class PersonAgeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    def __init__(
            self,
            age_shift_metadata: Optional[AgeShiftMetadata] = default_age_shift_metadata
    ):
        super().__init__()
        self.metadata = age_shift_metadata

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["metadata"] = self.metadata.to_payload()

        return result

default_person_age_generator_metadata = PersonAgeGeneratorMetadata()