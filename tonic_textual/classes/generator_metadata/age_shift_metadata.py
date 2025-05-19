from typing import Dict


class AgeShiftMetadata:
    def __init__(
            self,
            age_shift_in_years: int = 7
    ):
        self.age_shift_in_years = age_shift_in_years

    def to_payload(self) -> Dict:
        result = dict()

        result["ageShiftInYears"] = self.age_shift_in_years        

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "AgeShiftMetadata":
        result = AgeShiftMetadata()

        result.age_shift_in_years = payload.get("ageShiftInYears", default_age_shift_metadata.age_shift_in_years)

        return result

default_age_shift_metadata = AgeShiftMetadata()