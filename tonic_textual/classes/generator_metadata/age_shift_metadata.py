from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class AgeShiftMetadata(BaseMetadata):
    age_shift_in_years: int
    bin_age_into_ranges: bool

    def __init__(self):
        super().__init__()
        self.age_shift_in_years = 7
        self.bin_age_into_ranges = False

    def __eq__(self, other: "AgeShiftMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.age_shift_in_years != other.age_shift_in_years:
            return False

        if self.bin_age_into_ranges != other.bin_age_into_ranges:
            return False

        return True

    def to_payload(self, default: "AgeShiftMetadata") -> Dict:
        result = super().to_payload(default)

        if self.age_shift_in_years != default.age_shift_in_years:
            result["ageShiftInYears"] = self.age_shift_in_years

        if self.bin_age_into_ranges != default.bin_age_into_ranges:
            result["binAgeIntoRanges"] = self.bin_age_into_ranges

        return result


default_age_shift_metadata = AgeShiftMetadata()
def age_shift_metadata_to_payload(metadata: AgeShiftMetadata) -> Dict:
    return metadata.to_payload(default_age_shift_metadata)