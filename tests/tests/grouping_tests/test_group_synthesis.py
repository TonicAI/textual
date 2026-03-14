from unittest.mock import MagicMock, patch

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)
from tonic_textual.redact_api import TextualNer


# --- Helpers ---

def _make_replacement(start, end, label, text, score=0.95, language="en", **kwargs):
    return Replacement(
        start=start,
        end=end,
        new_start=start,
        new_end=end + 5,
        label=label,
        text=text,
        score=score,
        language=language,
        **kwargs,
    )


def _make_detection(start, end, label, text, score=0.95):
    return SingleDetectionResult(
        start=start,
        end=end,
        label=label,
        text=text,
        score=score,
    )


def _make_textual_ner():
    """Create a TextualNer with a mocked HTTP client."""
    with patch("tonic_textual.redact_api.HttpClient"):
        ner = TextualNer(base_url="https://fake", api_key="fake-key")
    ner.client = MagicMock()
    return ner


def _api_replacement(start, end, label, text, new_text, score=0.95, language="en"):
    """Build a replacement dict as the API would return it (camelCase keys)."""
    return {
        "start": start,
        "end": end,
        "newStart": start,
        "newEnd": start + len(new_text),
        "label": label,
        "text": text,
        "newText": new_text,
        "score": score,
        "language": language,
    }


# --- Tests for group_synthesis method ---

class TestGroupSynthesis:
    def test_single_replacement(self):
        ner = _make_textual_ner()
        text = "Hello John Smith"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex Smith",
            "replacements": [
                _api_replacement(6, 10, "NAME_GIVEN", "John", "Alex"),
            ],
        }

        result = ner.group_synthesis(reps, text)

        assert isinstance(result, RedactionResponse)
        assert result.redacted_text == "Hello Alex Smith"
        assert result.original_text == text
        assert len(result.de_identify_results) == 1
        assert isinstance(result.de_identify_results[0], Replacement)
        assert result.de_identify_results[0].text == "John"
        assert result.de_identify_results[0].new_text == "Alex"
        assert result.de_identify_results[0].label == "NAME_GIVEN"

    def test_multiple_replacements(self):
        ner = _make_textual_ner()
        text = "John Smith met with Jane Doe"
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(5, 10, "NAME_FAMILY", "Smith"),
            _make_replacement(20, 24, "NAME_GIVEN", "Jane"),
            _make_replacement(25, 28, "NAME_FAMILY", "Doe"),
        ]

        ner.client.http_post.return_value = {
            "redacted_text": "Alex Jones met with Beth Miller",
            "replacements": [
                _api_replacement(0, 4, "NAME_GIVEN", "John", "Alex"),
                _api_replacement(5, 10, "NAME_FAMILY", "Smith", "Jones"),
                _api_replacement(20, 24, "NAME_GIVEN", "Jane", "Beth"),
                _api_replacement(25, 28, "NAME_FAMILY", "Doe", "Miller"),
            ],
        }

        result = ner.group_synthesis(reps, text)

        assert result.redacted_text == "Alex Jones met with Beth Miller"
        assert len(result.de_identify_results) == 4
        assert result.de_identify_results[0].text == "John"
        assert result.de_identify_results[0].new_text == "Alex"
        assert result.de_identify_results[1].text == "Smith"
        assert result.de_identify_results[1].new_text == "Jones"
        assert result.de_identify_results[2].text == "Jane"
        assert result.de_identify_results[2].new_text == "Beth"
        assert result.de_identify_results[3].text == "Doe"
        assert result.de_identify_results[3].new_text == "Miller"

    def test_empty_replacements(self):
        ner = _make_textual_ner()
        text = "No entities here"

        ner.client.http_post.return_value = {
            "redacted_text": "No entities here",
            "replacements": [],
        }

        result = ner.group_synthesis([], text)

        assert result.redacted_text == "No entities here"
        assert result.original_text == text
        assert result.de_identify_results == []

    def test_calls_correct_endpoint(self):
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [],
        }

        ner.group_synthesis(reps, text)

        ner.client.http_post.assert_called_once()
        call_args = ner.client.http_post.call_args
        assert call_args[0][0] == "/api/synthesis/group_synthesis"

    def test_payload_sent_to_api(self):
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [],
        }

        ner.group_synthesis(reps, text)

        call_args = ner.client.http_post.call_args
        payload = call_args[1]["data"] if "data" in call_args[1] else call_args[0][1]
        assert payload["original_text"] == text
        assert len(payload["entities"]) == 1
        assert payload["entities"][0]["text"] == "John"

    def test_replacement_fields_parsed(self):
        """Verify all camelCase API fields are mapped to Replacement attributes."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [{
                "start": 6,
                "end": 10,
                "newStart": 6,
                "newEnd": 10,
                "label": "NAME_GIVEN",
                "text": "John",
                "newText": "Alex",
                "score": 0.95,
                "language": "en",
            }],
        }

        result = ner.group_synthesis(reps, text)
        rep = result.de_identify_results[0]

        assert rep.start == 6
        assert rep.end == 10
        assert rep.new_start == 6
        assert rep.new_end == 10
        assert rep.label == "NAME_GIVEN"
        assert rep.text == "John"
        assert rep.new_text == "Alex"
        assert rep.score == 0.95
        assert rep.language == "en"

    def test_return_type_is_redaction_response(self):
        ner = _make_textual_ner()
        text = "John and Jane"
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(9, 13, "NAME_GIVEN", "Jane"),
        ]

        ner.client.http_post.return_value = {
            "redacted_text": "Alex and Beth",
            "replacements": [
                _api_replacement(0, 4, "NAME_GIVEN", "John", "Alex"),
                _api_replacement(9, 13, "NAME_GIVEN", "Jane", "Beth"),
            ],
        }

        result = ner.group_synthesis(reps, text)

        assert isinstance(result, RedactionResponse)
        assert isinstance(result.de_identify_results, list)
        for rep in result.de_identify_results:
            assert isinstance(rep, Replacement)

    def test_with_single_detection_result_input(self):
        ner = _make_textual_ner()
        text = "Hello John"
        detections = [_make_detection(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [
                _api_replacement(6, 10, "NAME_GIVEN", "John", "Alex"),
            ],
        }

        result = ner.group_synthesis(detections, text)

        assert len(result.de_identify_results) == 1
        assert result.de_identify_results[0].text == "John"

    def test_with_dict_input(self):
        ner = _make_textual_ner()
        text = "Hello John"
        dict_entities = [
            {"start": 6, "end": 10, "label": "NAME_GIVEN", "text": "John", "score": 0.95}
        ]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [
                _api_replacement(6, 10, "NAME_GIVEN", "John", "Alex"),
            ],
        }

        result = ner.group_synthesis(dict_entities, text)

        assert len(result.de_identify_results) == 1
        assert result.de_identify_results[0].text == "John"

    def test_response_missing_replacements_key(self):
        """If the response has no 'replacements' key, de_identify_results should be empty."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
        }

        result = ner.group_synthesis(reps, text)

        assert result.redacted_text == "Hello Alex"
        assert result.de_identify_results == []

    def test_response_missing_redacted_text_key(self):
        """If the response has no 'redacted_text' key, redacted_text defaults to empty string."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "replacements": [],
        }

        result = ner.group_synthesis(reps, text)

        assert result.redacted_text == ""

    def test_usage_from_response(self):
        """If the API returns a usage field, it should be passed through."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [],
            "usage": 42,
        }

        result = ner.group_synthesis(reps, text)

        assert result.usage == 42

    def test_usage_defaults_to_zero(self):
        """If the API does not return a usage field, it should default to 0."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Hello Alex",
            "replacements": [],
        }

        result = ner.group_synthesis(reps, text)

        assert result.usage == 0

    def test_duplicate_entities_synthesized_consistently(self):
        """When the same entity appears multiple times, the API should return
        consistent synthesis for all occurrences."""
        ner = _make_textual_ner()
        text = "John went to the store. John came back."
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(24, 28, "NAME_GIVEN", "John"),
        ]

        ner.client.http_post.return_value = {
            "redacted_text": "Alex went to the store. Alex came back.",
            "replacements": [
                _api_replacement(0, 4, "NAME_GIVEN", "John", "Alex"),
                _api_replacement(24, 28, "NAME_GIVEN", "John", "Alex"),
            ],
        }

        result = ner.group_synthesis(reps, text)

        assert len(result.de_identify_results) == 2
        assert result.de_identify_results[0].new_text == "Alex"
        assert result.de_identify_results[1].new_text == "Alex"

    def test_original_text_preserved(self):
        """The original_text on the response should always be the input text."""
        ner = _make_textual_ner()
        text = "John Smith met Jane Doe"
        reps = [_make_replacement(0, 4, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "redacted_text": "Alex Smith met Jane Doe",
            "replacements": [
                _api_replacement(0, 4, "NAME_GIVEN", "John", "Alex"),
            ],
        }

        result = ner.group_synthesis(reps, text)

        assert result.original_text == text
