from typing import Dict


class AgeShiftMetadata(dict):
    """Configuration for the age shift amount used by
    :class:`PersonAgeGeneratorMetadata`.

    Defines how many years to shift detected ages by.

    Parameters
    ----------
    age_shift_in_years : int
        The number of years to shift the age. Default is ``7``.
    apply_constant_shift_to_document : bool
        When ``True``, every detected age in the same document is shifted by
        the same number of years. This preserves relative age differences
        between people mentioned in the document. Default is ``False``.
    """

    def __init__(
            self,
            age_shift_in_years: int = 7,
            apply_constant_shift_to_document: bool = False
    ):
        super().__init__()
        self["_type"] = self.__class__.__name__
        self["ageShiftInYears"] = age_shift_in_years
        self["applyConstantShiftToDocument"] = apply_constant_shift_to_document

    @property
    def age_shift_in_years(self) -> int:
        return self["ageShiftInYears"]

    @age_shift_in_years.setter
    def age_shift_in_years(self, value: int):
        self["ageShiftInYears"] = value

    @property
    def apply_constant_shift_to_document(self) -> bool:
        return self["applyConstantShiftToDocument"]

    @apply_constant_shift_to_document.setter
    def apply_constant_shift_to_document(self, value: bool):
        self["applyConstantShiftToDocument"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "AgeShiftMetadata":
        return AgeShiftMetadata(
            age_shift_in_years=payload.get("ageShiftInYears", 7),
            apply_constant_shift_to_document=payload.get("applyConstantShiftToDocument", False)
        )

default_age_shift_metadata = AgeShiftMetadata()
