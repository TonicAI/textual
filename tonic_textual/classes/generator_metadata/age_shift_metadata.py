from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class AgeShiftMetadata(BaseMetadata):
    def __init__(self, age_shift_in_years: Optional[int] = 7):
        super().__init__()
        self.age_shift_in_years = age_shift_in_years

    def to_payload(self, default: "AgeShiftMetadata") -> Dict:
        result = super().to_payload(default)

        result["ageShiftInYears"] = self.age_shift_in_years        

        return result


default_age_shift_metadata = AgeShiftMetadata()
def age_shift_metadata_to_payload(metadata: AgeShiftMetadata) -> Dict:
    return metadata.to_payload(default_age_shift_metadata)