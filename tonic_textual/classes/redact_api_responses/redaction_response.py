from typing import List

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)


class RedactionResponse(dict):
    """Redaction response object

    Attributes
    ----------
    original_text : str
        The original text
    redacted_text : str
        The redacted/synthesized text
    usage : int
        The number of words used
    de_identify_results : List[Replacement]
        The list of named entities found in original_text
    """
    def __init__(
        self,
        original_text: str,
        redacted_text: str,
        usage: int,
        de_identify_results: List[Replacement],
    ):
        self.original_text = original_text
        self.redacted_text = redacted_text
        self.usage = usage
        self.de_identify_results = de_identify_results
        dict.__init__(
            self,
            original_text=original_text,
            redacted_text=redacted_text,
            usage=usage,
            de_identify_results=de_identify_results,
        )

    def describe(self) -> str:
        result = f"{self.redacted_text}\n"
        for x in self.de_identify_results:
            result += f"{x.describe()}\n"
        return result

    def get_usage(self):
        return self.usage
