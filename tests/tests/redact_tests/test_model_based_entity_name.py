import json

import pytest

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.generator_utils import replacement_to_grouping_entity
from tonic_textual.redact_api import TextualNer


ENTITY = {
    "start": 0,
    "end": 6,
    "newStart": 0,
    "newEnd": 18,
    "label": "MEDICAL_HEIGHT",
    "text": "six ft",
    "newText": "[MEDICAL_HEIGHT]",
    "score": 0.98,
    "language": "en",
    "modelBasedEntityName": "MEDICAL_MEASUREMENT",
}


def test_replacement_serializes_model_based_entity_name_when_present():
    replacement = Replacement(
        start=0,
        end=6,
        new_start=0,
        new_end=18,
        label="MEDICAL_HEIGHT",
        text="six ft",
        score=0.98,
        language="en",
        model_based_entity_name="MEDICAL_MEASUREMENT",
    )

    assert replacement.model_based_entity_name == "MEDICAL_MEASUREMENT"
    assert replacement.to_dict()["model_based_entity_name"] == "MEDICAL_MEASUREMENT"
    assert json.loads(json.dumps(replacement))["model_based_entity_name"] == "MEDICAL_MEASUREMENT"


def test_replacement_omits_model_based_entity_name_when_absent():
    replacement = Replacement(
        start=0,
        end=4,
        new_start=0,
        new_end=4,
        label="NAME_GIVEN",
        text="John",
        score=0.95,
        language="en",
    )

    assert replacement.model_based_entity_name is None
    assert "model_based_entity_name" not in replacement.to_dict()
    assert "model_based_entity_name" not in replacement


@pytest.fixture
def offline_ner(monkeypatch):
    ner = TextualNer("http://localhost", api_key="fake-key")
    responses = {
        "/api/redact": {
            "originalText": "six ft",
            "redactedText": "[MEDICAL_HEIGHT]",
            "usage": 2,
            "deIdentifyResults": [ENTITY],
        },
        "/api/redact/bulk": {
            "bulkText": ["six ft"],
            "bulkRedactedText": ["[MEDICAL_HEIGHT]"],
            "usage": 2,
            "deIdentifyResults": [{**ENTITY, "idx": 0}],
        },
        "/api/synthesis/group": {
            "groups": [{"representative": "six ft", "entities": [ENTITY]}],
        },
    }
    monkeypatch.setattr(ner.client, "http_post", lambda url, **_: responses[url])
    return ner


def test_single_redaction_preserves_model_based_entity_name(offline_ner):
    response = offline_ner.send_redact_request("/api/redact", {})

    assert response.de_identify_results[0].model_based_entity_name == "MEDICAL_MEASUREMENT"


def test_bulk_redaction_preserves_model_based_entity_name(offline_ner):
    response = offline_ner.send_redact_bulk_request("/api/redact/bulk", {})

    assert response.de_identify_results[0][0].model_based_entity_name == "MEDICAL_MEASUREMENT"


def test_grouping_round_trip_preserves_model_based_entity_name(offline_ner):
    replacement = Replacement(
        start=0,
        end=6,
        new_start=0,
        new_end=18,
        label="MEDICAL_HEIGHT",
        text="six ft",
        score=0.98,
        language="en",
        model_based_entity_name="MEDICAL_MEASUREMENT",
    )

    payload_entity = replacement_to_grouping_entity(replacement, "six ft")
    response = offline_ner.group_entities([replacement], "six ft")

    assert payload_entity["modelBasedEntityName"] == "MEDICAL_MEASUREMENT"
    assert response.groups[0].entities[0].model_based_entity_name == "MEDICAL_MEASUREMENT"
