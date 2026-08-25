import math

import pytest

from tests.utils.redact_utils import create_custom_entity, delete_custom_entity
from tonic_textual.classes.tonic_exception import (
    InvalidJsonForRedactionRequest,
    TextualServerBadRequest,
)
from tonic_textual.generator_utils import generate_redact_payload
from tonic_textual.redact_api import TextualNer

SINGLE_RESPONSE = {
    "originalText": "John Smith is a person",
    "redactedText": "[NAME_GIVEN_x] [NAME_FAMILY_y] is a person",
    "usage": 5,
    "deIdentifyResults": [],
}

BULK_RESPONSE = {
    "bulkText": ["John Smith is a person", "I live in Atlanta"],
    "bulkRedactedText": [
        "[NAME_GIVEN_x] [NAME_FAMILY_y] is a person",
        "I live in [LOCATION_CITY_z]",
    ],
    "usage": 9,
    "deIdentifyResults": [],
}

METHOD_CASES = [
    ("redact", "John Smith is a person", "/api/redact", SINGLE_RESPONSE),
    (
        "redact_bulk",
        ["John Smith is a person", "I live in Atlanta"],
        "/api/redact/bulk",
        BULK_RESPONSE,
    ),
    ("redact_json", '{"name": "John Smith"}', "/api/redact/json", SINGLE_RESPONSE),
    (
        "redact_xml",
        "<root><name>John Smith</name></root>",
        "/api/redact/xml",
        SINGLE_RESPONSE,
    ),
    ("redact_html", "<p>John Smith</p>", "/api/redact/html", SINGLE_RESPONSE),
]

METHOD_IDS = [case[0] for case in METHOD_CASES]


@pytest.fixture
def make_mocked_ner(monkeypatch):
    """Builds a TextualNer whose http_post is replaced with a stub that records
    the request payload and returns a canned response."""

    def _make(response):
        ner = TextualNer(base_url="http://localhost", api_key="fake-key")
        requests_made = []

        def fake_http_post(
            url, params={}, data={}, files={}, additional_headers={}, timeout_seconds=None
        ):
            requests_made.append({"url": url, "data": data})
            return response

        monkeypatch.setattr(ner.client, "http_post", fake_http_post)
        return ner, requests_made

    return _make


@pytest.mark.parametrize("method_name,input_data,endpoint,response", METHOD_CASES, ids=METHOD_IDS)
def test_confidence_thresholds_are_sent_in_payload(
    make_mocked_ner, method_name, input_data, endpoint, response
):
    ner, requests_made = make_mocked_ner(response)

    getattr(ner, method_name)(
        input_data,
        custom_entities=["ENTITY_A", "ENTITY_B"],
        custom_entity_confidence_thresholds={
            "ENTITY_A": 0.5,
            "ENTITY_B": 1.0,
        },
    )

    assert len(requests_made) == 1
    assert requests_made[0]["url"] == endpoint

    payload = requests_made[0]["data"]
    assert payload["customPiiEntityIds"] == ["ENTITY_A", "ENTITY_B"]
    assert payload["customEntityConfidenceThresholds"] == {
        "ENTITY_A": 0.5,
        "ENTITY_B": 1.0,
    }
    # Preserve numeric type so JSON serialization matches the backend contract.
    for value in payload["customEntityConfidenceThresholds"].values():
        assert isinstance(value, (int, float))
        assert not isinstance(value, bool)


@pytest.mark.parametrize("method_name,input_data,endpoint,response", METHOD_CASES, ids=METHOD_IDS)
def test_confidence_thresholds_are_omitted_when_not_supplied(
    make_mocked_ner, method_name, input_data, endpoint, response
):
    ner, requests_made = make_mocked_ner(response)

    getattr(ner, method_name)(input_data, custom_entities=["ENTITY_A"])

    assert len(requests_made) == 1
    assert "customEntityConfidenceThresholds" not in requests_made[0]["data"]


INVALID_THRESHOLD_CASES = [
    ("zero", 0),
    ("negative", -0.1),
    ("above-one", 1.1),
    ("nan", math.nan),
    ("positive-infinity", math.inf),
    ("negative-infinity", -math.inf),
    ("non-numeric-string", "0.5"),
    ("non-numeric-none", None),
]


@pytest.mark.parametrize("method_name,input_data,endpoint,response", METHOD_CASES, ids=METHOD_IDS)
@pytest.mark.parametrize(
    "bad_value",
    [case[1] for case in INVALID_THRESHOLD_CASES],
    ids=[case[0] for case in INVALID_THRESHOLD_CASES],
)
def test_invalid_confidence_threshold_raises_before_request_is_sent(
    make_mocked_ner, method_name, input_data, endpoint, response, bad_value
):
    ner, requests_made = make_mocked_ner(response)

    with pytest.raises(Exception, match="Invalid value for custom entity confidence thresholds"):
        getattr(ner, method_name)(
            input_data,
            custom_entities=["ENTITY_A"],
            custom_entity_confidence_thresholds={"ENTITY_A": bad_value},
        )

    assert len(requests_made) == 0


def test_generate_redact_payload_serializes_confidence_thresholds():
    payload = generate_redact_payload(
        custom_entities=["ENTITY_A", "ENTITY_B"],
        custom_entity_confidence_thresholds={
            "ENTITY_A": 0.25,
            "ENTITY_B": 1,
        },
    )

    assert payload["customEntityConfidenceThresholds"] == {
        "ENTITY_A": 0.25,
        "ENTITY_B": 1,
    }


def test_generate_redact_payload_omits_confidence_thresholds_by_default():
    payload = generate_redact_payload(custom_entities=["ENTITY_A"])

    assert "customEntityConfidenceThresholds" not in payload


@pytest.mark.parametrize(
    "threshold",
    [0.1, 0.5, 1.0],
    ids=["low", "mid", "boundary-one"],
)
def test_redact_with_custom_entity_confidence_thresholds(textual, threshold):
    custom_entity = create_custom_entity(textual, ["hovercraft"])
    custom_entity_name = custom_entity["name"]
    try:
        response = textual.redact(
            "John Smith owns a hovercraft.",
            custom_entities=[custom_entity_name],
            custom_entity_confidence_thresholds={custom_entity_name: threshold},
        )

        assert response is not None
    finally:
        delete_custom_entity(textual, custom_entity_name)


def test_confidence_threshold_for_unrequested_entity_is_rejected(textual):
    with pytest.raises((TextualServerBadRequest, InvalidJsonForRedactionRequest)):
        textual.redact(
            "John Smith is a person",
            custom_entity_confidence_thresholds={"NOT_A_REQUESTED_ENTITY": 0.5},
        )
