from enum import Enum


class Casing(str, Enum):
    MixedCase = "MixedCase"
    AllLowerCase = "AllLowerCase"
    AllUpperCase = "AllUpperCase"


