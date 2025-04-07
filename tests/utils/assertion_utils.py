from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)


def assert_redaction_response_equal(
    r1: RedactionResponse, r2: RedactionResponse
) -> bool:
    assert r1["original_text"] == r2["original_text"]
    assert r1["redacted_text"] == r2["redacted_text"]
    assert r1["usage"] == r2["usage"]
    assert len(r1["de_identify_results"]) == len(r2["de_identify_results"])
    for d1, d2 in zip(r1["de_identify_results"], r2["de_identify_results"]):
        assert_replacements_are_equal(d1, d2)


def assert_replacements_are_equal(r1: Replacement, r2: Replacement):
    assert r1["start"] == r2["start"]
    assert r1["end"] == r2["end"]
    assert r1["new_start"] == r2["new_start"]
    assert r1["new_end"] == r2["new_end"]
    assert r1["label"] == r2["label"]
    assert r1["text"] == r2["text"]
    assert r1["score"] == r2["score"]
    assert r1["language"] == r2["language"]
    assert r1["new_text"] == r2["new_text"]
