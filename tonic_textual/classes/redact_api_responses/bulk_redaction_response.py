from typing import List

from tonic_textual.classes.common_api_responses.replacement import Replacement


class BulkRedactionResponse(dict):
    """Bulk Redaction response object

    Attributes
    ----------
    bulk_text : List[str]
        The original text.
    bulk_redacted_text : List[str]
        The redacted and synthesized text.
    usage : int
        The number of words used
    de_identify_results : List[Replacement]
        The list of named entities that were found in bulk_text.
    """

    def __init__(
        self,
        bulk_text: List[str],
        bulk_redacted_text: List[str],
        usage: int,
        de_identify_results: List[Replacement],
    ):
        self.bulk_text = bulk_text
        self.bulk_redacted_text = bulk_redacted_text
        self.usage = usage
        self.de_identify_results = de_identify_results
        dict.__init__(
            self,
            bulk_text=bulk_text,
            bulk_redacted_text=bulk_redacted_text,
            usage=usage,
            de_identify_results=de_identify_results,
        )

    def describe(self) -> str:

        result = ""
        for redacted_text, de_id_res in zip(
            self.bulk_redacted_text, self.de_identify_results
        ):
            result += f"{redacted_text}\n"
            for replacement in de_id_res:
                result += f"{replacement.describe()}\n"
        return result

    def get_usage(self):
        return self.usage
