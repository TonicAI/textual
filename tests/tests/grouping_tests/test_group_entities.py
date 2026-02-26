from unittest.mock import MagicMock, patch

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.generator_utils import (
    generate_grouping_playload,
    replacement_to_grouping_entity,
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


# --- Tests for replacement_to_grouping_entity ---

class TestReplacementToGroupingEntity:
    def test_basic_ascii_text(self):
        text = "Hello John Smith"
        rep = _make_replacement(6, 10, "NAME_GIVEN", "John")

        result = replacement_to_grouping_entity(rep, text)

        assert result["pythonStart"] == 6
        assert result["pythonEnd"] == 10
        assert result["label"] == "NAME_GIVEN"
        assert result["text"] == "John"
        assert result["score"] == 0.95

    def test_ascii_utf16_offsets_match_python(self):
        """For pure ASCII text, UTF-16 and Python offsets should be the same."""
        text = "Hello John Smith"
        rep = _make_replacement(6, 10, "NAME_GIVEN", "John")

        result = replacement_to_grouping_entity(rep, text)

        assert result["start"] == result["pythonStart"]
        assert result["end"] == result["pythonEnd"]

    def test_emoji_utf16_offsets_differ(self):
        """Emoji characters take 2 UTF-16 code units, so offsets diverge."""
        # '😀' is a surrogate pair in UTF-16 (2 code units), but 1 Python char
        text = "😀 John Smith"
        # In Python: '😀'=index 0, ' '=1, 'J'=2, 'o'=3, 'h'=4, 'n'=5
        rep = _make_replacement(2, 6, "NAME_GIVEN", "John")

        result = replacement_to_grouping_entity(rep, text)

        assert result["pythonStart"] == 2
        assert result["pythonEnd"] == 6
        # UTF-16: '😀' takes indices 0-1, ' '=2, 'J'=3, 'o'=4, 'h'=5, 'n'=6
        assert result["start"] == 3
        assert result["end"] == 7

    def test_with_single_detection_result_input(self):
        text = "Hello John"
        det = _make_detection(6, 10, "NAME_GIVEN", "John")

        result = replacement_to_grouping_entity(det, text)

        assert result["pythonStart"] == 6
        assert result["pythonEnd"] == 10
        assert result["label"] == "NAME_GIVEN"
        assert result["text"] == "John"

    def test_with_dict_input(self):
        text = "Hello John"
        entity_dict = {
            "start": 6,
            "end": 10,
            "label": "NAME_GIVEN",
            "text": "John",
            "score": 0.9,
        }

        result = replacement_to_grouping_entity(entity_dict, text)

        assert result["pythonStart"] == 6
        assert result["pythonEnd"] == 10
        assert result["label"] == "NAME_GIVEN"
        assert result["text"] == "John"
        assert result["score"] == 0.9

    def test_entity_at_start_of_text(self):
        text = "John went home"
        rep = _make_replacement(0, 4, "NAME_GIVEN", "John")

        result = replacement_to_grouping_entity(rep, text)

        assert result["pythonStart"] == 0
        assert result["start"] == 0


# --- Tests for generate_grouping_playload ---

class TestGenerateGroupingPayload:
    def test_basic_payload_structure(self):
        text = "Hello John Smith"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        payload = generate_grouping_playload(reps, text)

        assert "entities" in payload
        assert "original_text" in payload
        assert payload["original_text"] == text
        assert len(payload["entities"]) == 1

    def test_multiple_entities(self):
        text = "Hello John Smith and Jane Doe"
        reps = [
            _make_replacement(6, 10, "NAME_GIVEN", "John"),
            _make_replacement(11, 16, "NAME_FAMILY", "Smith"),
            _make_replacement(21, 25, "NAME_GIVEN", "Jane"),
        ]

        payload = generate_grouping_playload(reps, text)

        assert len(payload["entities"]) == 3
        assert payload["entities"][0]["text"] == "John"
        assert payload["entities"][1]["text"] == "Smith"
        assert payload["entities"][2]["text"] == "Jane"

    def test_empty_entities(self):
        text = "No entities here"

        payload = generate_grouping_playload([], text)

        assert payload["entities"] == []
        assert payload["original_text"] == text

    def test_mixed_input_types(self):
        text = "John Smith john@example.com"
        inputs = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_detection(5, 10, "NAME_FAMILY", "Smith"),
            {"start": 11, "end": 27, "label": "EMAIL_ADDRESS", "text": "john@example.com", "score": 0.99},
        ]

        payload = generate_grouping_playload(inputs, text)

        assert len(payload["entities"]) == 3
        assert payload["entities"][0]["label"] == "NAME_GIVEN"
        assert payload["entities"][1]["label"] == "NAME_FAMILY"
        assert payload["entities"][2]["label"] == "EMAIL_ADDRESS"

    def test_entities_include_utf16_offsets(self):
        text = "Hello John Smith"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        payload = generate_grouping_playload(reps, text)
        entity = payload["entities"][0]

        assert "start" in entity
        assert "end" in entity
        assert "pythonStart" in entity
        assert "pythonEnd" in entity


# --- Tests for group_entities method ---

class TestGroupEntities:
    def test_single_group_single_entity(self):
        ner = _make_textual_ner()
        text = "Hello John Smith"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 6, "end": 10, "label": "NAME_GIVEN", "text": "John", "score": 0.95}
                    ]
                }
            ]
        }

        result = ner.group_entities(reps, text)

        assert len(result) == 1
        assert len(result[0]) == 1
        assert isinstance(result[0][0], SingleDetectionResult)
        assert result[0][0].start == 6
        assert result[0][0].label == "NAME_GIVEN"
        assert result[0][0].text == "John"
        assert result[0][0].score == 0.95

    def test_multiple_groups(self):
        ner = _make_textual_ner()
        text = "John Smith and john@example.com"
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(5, 10, "NAME_FAMILY", "Smith"),
            _make_replacement(15, 31, "EMAIL_ADDRESS", "john@example.com"),
        ]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 0, "end": 4, "label": "NAME_GIVEN", "text": "John", "score": 0.95},
                        {"start": 5, "end": 10, "label": "NAME_FAMILY", "text": "Smith", "score": 0.90},
                    ]
                },
                {
                    "entities": [
                        {"start": 15, "end": 31, "label": "EMAIL_ADDRESS", "text": "john@example.com", "score": 0.99},
                    ]
                },
            ]
        }

        result = ner.group_entities(reps, text)

        assert len(result) == 2
        assert len(result[0]) == 2
        assert len(result[1]) == 1
        assert result[0][0].text == "John"
        assert result[0][1].text == "Smith"
        assert result[1][0].text == "john@example.com"

    def test_empty_response(self):
        ner = _make_textual_ner()
        text = "No entities"

        ner.client.http_post.return_value = {"groups": []}

        result = ner.group_entities([], text)

        assert result == []

    def test_group_with_multiple_same_entity(self):
        """Entities with the same text in different locations should be grouped together."""
        ner = _make_textual_ner()
        text = "John went to the store. John came back."
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(24, 28, "NAME_GIVEN", "John"),
        ]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 0, "end": 4, "label": "NAME_GIVEN", "text": "John", "score": 0.95},
                        {"start": 24, "end": 28, "label": "NAME_GIVEN", "text": "John", "score": 0.92},
                    ]
                }
            ]
        }

        result = ner.group_entities(reps, text)

        assert len(result) == 1
        assert len(result[0]) == 2
        assert result[0][0].start == 0
        assert result[0][1].start == 24

    def test_calls_correct_endpoint(self):
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {"groups": []}

        ner.group_entities(reps, text)

        ner.client.http_post.assert_called_once()
        call_args = ner.client.http_post.call_args
        assert call_args[0][0] == "/api/synthesis/group"

    def test_payload_sent_to_api(self):
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {"groups": []}

        ner.group_entities(reps, text)

        call_args = ner.client.http_post.call_args
        payload = call_args[1]["data"] if "data" in call_args[1] else call_args[0][1]
        assert payload["original_text"] == text
        assert len(payload["entities"]) == 1
        assert payload["entities"][0]["text"] == "John"

    def test_return_type_is_list_of_lists(self):
        ner = _make_textual_ner()
        text = "John and Jane"
        reps = [
            _make_replacement(0, 4, "NAME_GIVEN", "John"),
            _make_replacement(9, 13, "NAME_GIVEN", "Jane"),
        ]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 0, "end": 4, "label": "NAME_GIVEN", "text": "John", "score": 0.95},
                    ]
                },
                {
                    "entities": [
                        {"start": 9, "end": 13, "label": "NAME_GIVEN", "text": "Jane", "score": 0.93},
                    ]
                },
            ]
        }

        result = ner.group_entities(reps, text)

        assert isinstance(result, list)
        for group in result:
            assert isinstance(group, list)
            for entity in group:
                assert isinstance(entity, SingleDetectionResult)

    def test_with_single_detection_result_input(self):
        ner = _make_textual_ner()
        text = "Hello John"
        detections = [_make_detection(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 6, "end": 10, "label": "NAME_GIVEN", "text": "John", "score": 0.95}
                    ]
                }
            ]
        }

        result = ner.group_entities(detections, text)

        assert len(result) == 1
        assert result[0][0].text == "John"

    def test_with_dict_input(self):
        ner = _make_textual_ner()
        text = "Hello John"
        dict_entities = [
            {"start": 6, "end": 10, "label": "NAME_GIVEN", "text": "John", "score": 0.95}
        ]

        ner.client.http_post.return_value = {
            "groups": [
                {
                    "entities": [
                        {"start": 6, "end": 10, "label": "NAME_GIVEN", "text": "John", "score": 0.95}
                    ]
                }
            ]
        }

        result = ner.group_entities(dict_entities, text)

        assert len(result) == 1
        assert result[0][0].text == "John"

    def test_response_missing_groups_key(self):
        """If the response has no 'groups' key, should return an empty list."""
        ner = _make_textual_ner()
        text = "Hello John"
        reps = [_make_replacement(6, 10, "NAME_GIVEN", "John")]

        ner.client.http_post.return_value = {}

        result = ner.group_entities(reps, text)

        assert result == []

    def test_group_with_empty_entities(self):
        """A group with an empty entities list results in an empty inner list."""
        ner = _make_textual_ner()
        text = "Hello"

        ner.client.http_post.return_value = {
            "groups": [
                {"entities": []}
            ]
        }

        result = ner.group_entities([], text)

        assert len(result) == 1
        assert result[0] == []
