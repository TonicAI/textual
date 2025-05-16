from typing import Dict, Optional


class AgeShiftMetadata:
    def __init__(
            self,
            age_shift_in_years: Optional[int] = 7
    ):
        self.age_shift_in_years = age_shift_in_years

    def to_payload(self) -> Dict:
        result = dict()

        result["ageShiftInYears"] = self.age_shift_in_years        

        return result

default_age_shift_metadata = AgeShiftMetadata()