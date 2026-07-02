"""Unit tests for the enable_llm_classification parameter.

These tests do not require a running Textual server. They verify that the
parameter is serialized into the request payload as the llmClassificationPolicy
property, and that it is omitted entirely when unset so requests remain
compatible with older servers.
"""

import pytest

from tonic_textual.generator_utils import generate_redact_payload
from tonic_textual.redact_api import TextualNer


class TestGenerateRedactPayload:
    def test_omitted_when_unset(self):
        payload = generate_redact_payload()
        assert "llmClassificationPolicy" not in payload

    def test_enabled(self):
        payload = generate_redact_payload(enable_llm_classification=True)
        assert payload["llmClassificationPolicy"] == "Enabled"

    def test_disabled(self):
        payload = generate_redact_payload(enable_llm_classification=False)
        assert payload["llmClassificationPolicy"] == "Disabled"


REDACT_RESPONSE = {
    "originalText": "x",
    "redactedText": "x",
    "usage": 1,
    "deIdentifyResults": [],
}
BULK_RESPONSE = {
    "bulkText": ["x"],
    "bulkRedactedText": ["x"],
    "usage": 1,
    "deIdentifyResults": [],
}


@pytest.fixture
def offline_ner(monkeypatch):
    """A TextualNer whose http_post captures the payload instead of calling a server."""
    ner = TextualNer("http://localhost", api_key="fake-key")
    captured = {}

    def fake_http_post(url, params={}, data={}, files={}, additional_headers={}, timeout_seconds=None):
        captured["url"] = url
        captured["payload"] = data
        return BULK_RESPONSE if url.endswith("/bulk") else REDACT_RESPONSE

    monkeypatch.setattr(ner.client, "http_post", fake_http_post)
    return ner, captured


REDACT_CALLS = [
    pytest.param(lambda ner, **kw: ner.redact("hello John", **kw), "/api/redact", id="redact"),
    pytest.param(lambda ner, **kw: ner.redact_bulk(["hello John"], **kw), "/api/redact/bulk", id="redact_bulk"),
    pytest.param(lambda ner, **kw: ner.redact_json('{"name": "John"}', **kw), "/api/redact/json", id="redact_json"),
    pytest.param(lambda ner, **kw: ner.redact_xml("<name>John</name>", **kw), "/api/redact/xml", id="redact_xml"),
    pytest.param(lambda ner, **kw: ner.redact_html("<html><body>John</body></html>", **kw), "/api/redact/html", id="redact_html"),
]


class TestRedactMethodsForwardLlmClassification:
    @pytest.mark.parametrize("call,endpoint", REDACT_CALLS)
    def test_enabled_is_sent(self, offline_ner, call, endpoint):
        ner, captured = offline_ner

        call(ner, enable_llm_classification=True)

        assert captured["url"] == endpoint
        assert captured["payload"]["llmClassificationPolicy"] == "Enabled"

    @pytest.mark.parametrize("call,endpoint", REDACT_CALLS)
    def test_disabled_is_sent(self, offline_ner, call, endpoint):
        ner, captured = offline_ner

        call(ner, enable_llm_classification=False)

        assert captured["url"] == endpoint
        assert captured["payload"]["llmClassificationPolicy"] == "Disabled"

    @pytest.mark.parametrize("call,endpoint", REDACT_CALLS)
    def test_omitted_by_default(self, offline_ner, call, endpoint):
        ner, captured = offline_ner

        call(ner)

        assert captured["url"] == endpoint
        assert "llmClassificationPolicy" not in captured["payload"]
