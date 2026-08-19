from tonic_textual.classes.subject_graph_collection import SubjectGraph


class _PdfClient:
    def __init__(self):
        self.call = None

    def http_get_file(self, url, session, params=None, additional_headers=None):
        params = params or {}
        additional_headers = additional_headers or {}
        self.call = (url, params, additional_headers)
        return b"%PDF-1.7\nsynthetic\n"


def test_render_pdf_downloads_retained_source_by_document_id():
    client = _PdfClient()
    graph = SubjectGraph(client, id="graph-id")

    content = graph.render_pdf("document-id", random_seed=42)

    assert content.startswith(b"%PDF-")
    assert client.call == (
        "/api/graph/graph-id/documents/document-id/render-pdf",
        {},
        {"textual-random-seed": "42"},
    )
