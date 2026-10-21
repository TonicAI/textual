import pytest

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)
from tonic_textual.helpers.json_conversation_helper import JsonConversationHelper


@pytest.mark.parametrize("separator", ["\n", " ", "", "\r\n", " | ", "🧬🔬"])
@pytest.mark.parametrize("redact_entities", [False, True])
def test_custom_separator_preserves_conversation_parts(separator, redact_entities):
    texts = ["Alice", "Bob", "Carol"]
    replacements = ["X", "[PERSON]", "Y"] if redact_entities else texts
    calls = []

    def redact(text):
        calls.append(text)
        entities = []
        original_start = redacted_start = 0
        for original, replacement in zip(texts, replacements):
            if redact_entities:
                entities.append(
                    Replacement(
                        original_start,
                        original_start + len(original),
                        redacted_start,
                        redacted_start + len(replacement),
                        "NAME",
                        original,
                        1.0,
                        "en",
                        replacement,
                    )
                )
            original_start += len(original) + len(separator)
            redacted_start += len(replacement) + len(separator)
        return RedactionResponse(text, separator.join(replacements), 3, entities)

    results = JsonConversationHelper().redact(
        {"messages": [{"text": text} for text in texts]},
        lambda conversation: conversation["messages"],
        lambda message: message["text"],
        redact,
        join_char=separator,
    )

    assert calls == [separator.join(texts)]
    assert [result.original_text for result in results] == texts
    assert [result.redacted_text for result in results] == replacements
    for result in results:
        assert len(result.de_identify_results) == int(redact_entities)
        for entity in result.de_identify_results:
            assert (entity.start, entity.end) == (0, len(result.original_text))
            assert (entity.new_start, entity.new_end) == (0, len(result.redacted_text))
            assert result.original_text[entity.start : entity.end] == entity.text
            assert (
                result.redacted_text[entity.new_start : entity.new_end]
                == entity.new_text
            )
