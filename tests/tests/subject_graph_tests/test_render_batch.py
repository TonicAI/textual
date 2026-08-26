import pytest

from tonic_textual.classes.subject_graph_collection import (
    MAX_RENDER_BATCH_ITEMS,
    MAX_RENDER_BATCH_UTF16_CODE_UNITS,
    SubjectGraph,
)
from tonic_textual.classes.tonic_exception import GraphRenderBatchError


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.content = b"{}"
        self.text = str(payload)

    def json(self):
        return self._payload


class _Client:
    def __init__(self, response):
        self.response = response
        self.call = None

    def http_post_raw(self, url, data=None, additional_headers=None, timeout_seconds=None):
        self.call = (url, data, additional_headers, timeout_seconds)
        return self.response


def _success_payload(items):
    return {
        "items": [
            {
                "documentId": item["documentId"],
                "statusCode": 200,
                "result": {"documentId": item["documentId"], "synthetic": item["text"].upper()},
                "error": None,
            }
            for item in items
        ]
    }


def test_render_documents_batch_posts_seeded_items_and_preserves_response_order():
    requested = [
        {"documentId": "doc-a", "text": "Alice"},
        {"documentId": "doc-b", "text": "Bob"},
    ]
    response = _Response(200, _success_payload(list(reversed(requested))))
    client = _Client(response)
    graph = SubjectGraph(client, id="graph-id")

    result = graph.render_documents_batch(requested, random_seed=42, timeout_seconds=17)

    assert [item["documentId"] for item in result["items"]] == ["doc-a", "doc-b"]
    assert client.call[0] == "/api/graph/graph-id/documents/render-batch"
    assert client.call[1] == {"items": [
        {"documentId": "doc-a", "text": "Alice", "seed": 42},
        {"documentId": "doc-b", "text": "Bob", "seed": 42},
    ]}
    assert client.call[2] == {"textual-random-seed": "42"}
    assert client.call[3] == 17


def test_render_documents_batch_validates_limits_and_seed_consistency():
    client = _Client(_Response(200, {"items": []}))
    graph = SubjectGraph(client, id="graph-id")

    with pytest.raises(ValueError, match="maximum is 500"):
        graph.render_documents_batch([
            {"documentId": str(index), "text": "x"}
            for index in range(MAX_RENDER_BATCH_ITEMS + 1)
        ])

    large = "😀" * (MAX_RENDER_BATCH_UTF16_CODE_UNITS // 2 + 1)
    with pytest.raises(ValueError, match="UTF-16 code units"):
        graph.render_documents_batch([{ "documentId": "large", "text": large }])

    with pytest.raises(ValueError, match="item seed must match"):
        graph.render_documents_batch([
            {"documentId": "doc-a", "text": "a", "seed": 1},
        ], random_seed=2)


def test_render_documents_batch_preserves_request_level_conflict_response():
    response = _Response(409, {
        "code": "projection_conflict",
        "message": "render projection is stale",
    })
    client = _Client(response)
    graph = SubjectGraph(client, id="graph-id")

    with pytest.raises(GraphRenderBatchError) as exc_info:
        graph.render_documents_batch([{ "documentId": "doc-a", "text": "a" }])

    assert exc_info.value.response is response
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "projection_conflict"
