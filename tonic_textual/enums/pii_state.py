from enum import Enum


class PiiState(str, Enum):
    Off = "Off"
    Synthesis = "Synthesis"
    Redaction = "Redaction"
