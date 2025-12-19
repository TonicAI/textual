from typing import Dict


class AgeShiftMetadata(dict):
    def __init__(
            self,
            age_shift_in_years: int = 7
    ):
        super().__init__()
        self["_type"] = self.__class__.__name__
        self["ageShiftInYears"] = age_shift_in_years

    @property
    def age_shift_in_years(self) -> int:
        return self["ageShiftInYears"]

    @age_shift_in_years.setter
    def age_shift_in_years(self, value: int):
        self["ageShiftInYears"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "AgeShiftMetadata":
        return AgeShiftMetadata(
            age_shift_in_years=payload.get("ageShiftInYears", 7)
        )

default_age_shift_metadata = AgeShiftMetadata()