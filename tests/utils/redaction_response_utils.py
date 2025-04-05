import json

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)


def build_redaction_response_from_json(j: str):
    d = json.loads(j)
    de_id_results = [
        Replacement(
            start=x["start"],
            end=x["end"],
            new_start=x.get("new_start"),
            new_end=x.get("new_end"),
            label=x["label"],
            text=x["text"],
            new_text=x.get("new_text"),
            score=x["score"],
            language=x.get("language"),
            example_redaction=x.get("example_redaction"),
            json_path=x.get("json_path"),
            xml_path=x.get("xml_path"),
        )
        for x in d["de_identify_results"]
    ]

    return RedactionResponse(
        d["original_text"],
        d["redacted_text"],
        d["usage"],
        de_id_results,
    )
