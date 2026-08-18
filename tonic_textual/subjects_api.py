import os
from typing import List, Optional
from warnings import warn
import requests

from tonic_textual.classes.subject_graph_collection import SubjectGraph

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.tonic_exception import (
    SubjectCollectionNameAlreadyExists,
)
from tonic_textual.services.dataset import DatasetService

class TextualSubjects:
    """Wrapper class to invoke the Tonic Textual API

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes. The default value is https://textual.tonic.ai.
    api_key : str
        Optional. Your API token. Instead of providing the API token
        here, we recommended that you set the API key in your environment as the
        value of TONIC_TEXTUAL_API_KEY.
    verify: bool
        Whether to verify SSL certification. By default, this is enabled.
    Examples
    --------
    >>> from tonic_textual.redact_api import TextualNer
    >>> textual = TextualNer()
    """

    def __init__(
        self,
        base_url: str = "https://textual.tonic.ai",
        api_key: Optional[str] = None,
        verify: bool = True,
    ):
        if api_key is None:
            api_key = os.environ.get("TONIC_TEXTUAL_API_KEY")
            if api_key is None:
                raise Exception(
                    "No API key provided. Either provide an API key, or set the API "
                    "key as the value of the TONIC_TEXTUAL_API_KEY environment "
                    "variable."
                )

        self.api_key = api_key
        self.client = HttpClient(base_url, self.api_key, verify)
        self.dataset_service = DatasetService(self.client)
        self.verify = verify
    def create_graph(
        self,
        name: Optional[str] = None,
        synthesize_labels: Optional[List[str]] = None,
        custom_pii_entity_ids: Optional[List[str]] = None,
        custom_pii_entities: Optional[dict] = None,
        label_block_lists: Optional[dict] = None,
    ) -> SubjectGraph:
        """Creates a subject graph — the dataset-free unit of the ``/api/graph`` streaming API.

        Unlike a subject collection, a graph does not expose a general file collection. You can stream
        raw text into it with ``SubjectGraph.add_text`` or upload standalone PDFs with
        ``SubjectGraph.add_pdf``. PDF sources are retained privately for later V5 rendering through
        ``SubjectGraph.render_pdf``; text remains caller-supplied at ``render_document`` time.

        Parameters
        ----------
        name : Optional[str] = None
            The name of the graph. Names must be unique. If no name is provided one is generated.
        synthesize_labels : Optional[List[str]] = None
            Built-in PII labels (e.g. ``"NAME_GIVEN"``, ``"EMAIL_ADDRESS"``) to SYNTHESIZE. When this
            or ``custom_pii_entity_ids`` is provided the graph uses an all-or-nothing config: ONLY
            these labels (and the custom entities) are synthesized and every other type is Off
            (detected then passed through unchanged). When both are omitted the graph keeps the broad
            default config.
        custom_pii_entity_ids : Optional[List[str]] = None
            Org-level custom-PII entity ids to detect AND synthesize (e.g. the Slack-mention
            ``username`` entity), so their custom label is detected at ingest and folded into the
            synthesis set. Requires the entities to exist server-side; on a standalone graph
            deployment (no Solar database) use ``custom_pii_entities`` instead.
        custom_pii_entities : Optional[dict] = None
            Custom regex entities defined INLINE (``{label: LabelCustomList(...).to_dict()}``), stored
            on the graph itself so no server-side entity lookup is needed. Each key becomes the
            detection label and is folded into the synthesis set — e.g.
            ``{"username": LabelCustomList(regexes=["(?<=<@)[^>]+(?=>)"]).to_dict()}`` detects Slack
            mentions as ``username``.
        label_block_lists : Optional[dict] = None
            Per-label block lists (``{label: LabelCustomList(...).to_dict()}``, same shape the dataset
            PUT used): values of that label that are DETECTED but NOT synthesized (passed through
            unchanged at render). Only honored alongside the all-or-nothing config.

        Returns
        -------
        SubjectGraph
            The newly created graph.

        Raises
        ------
        SubjectCollectionNameAlreadyExists
            Raised if a graph with the same name already exists.

        Examples
        --------
        >>> graph = tonic.create_graph("company_emails")
        """
        body: dict = {"name": name}
        if synthesize_labels is not None:
            body["synthesizeLabels"] = synthesize_labels
        if custom_pii_entity_ids is not None:
            body["customPiiEntityIds"] = custom_pii_entity_ids
        if custom_pii_entities is not None:
            body["customPiiEntities"] = custom_pii_entities
        if label_block_lists is not None:
            body["labelBlockLists"] = label_block_lists
        try:
            created = self.client.http_post("/api/graph", data=body)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise SubjectCollectionNameAlreadyExists(e)
            raise

        return SubjectGraph(self.client, id=created["id"], name=created.get("name"))

    def get_graph(self, graph_id: str) -> SubjectGraph:
        """Gets an existing subject graph by its id.

        Parameters
        ----------
        graph_id : str
            The id of the graph.

        Returns
        -------
        SubjectGraph

        Examples
        --------
        >>> graph = tonic.get_graph("f3c1...")
        """
        with requests.Session() as session:
            graph = self.client.http_get(f"/api/graph/{graph_id}", session=session)
        return SubjectGraph(self.client, id=graph["id"], name=graph.get("name"))

    def download_files(
        self,
        graph_name: str,
        files_dir: str,
        output_dir: str = "redacted",
    ) -> List[str]:
        """Downloads the redacted PDF for every file uploaded to a graph.

        A graph keeps NO copy of uploaded files — the PDF bytes are ephemeral (held on the ingest
        job only for the duration of processing, then discarded). So each original is RE-SUPPLIED
        from ``files_dir`` (matched by file name) and the graph's redacted-linking projection of it
        (a black box over each PII mention with the abbreviated structural token, e.g. ``p1_e`` /
        ``o1``) is saved to ``output_dir``.

        The graph must already be reconciled (so subjects/tokens exist). Only PDF file-documents are
        supported; text documents and files without a matching local original are skipped.

        Parameters
        ----------
        graph_name : str
            The name of the graph (or its id). Names must be unique; pass the id to disambiguate.
        files_dir : str
            Local folder holding the ORIGINAL files uploaded to the graph, searched recursively.
            Each document is matched to the file whose path relative to ``files_dir`` equals the
            name it was uploaded under.
        output_dir : str = "redacted"
            Folder to write the redacted PDFs to (source folder structure mirrored). Created if
            it does not exist.

        Returns
        -------
        List[str]
            The paths of the redacted PDFs written.

        Examples
        --------
        >>> tonic.download_files("company_pdfs", "./originals", "./redacted")
        """
        # Resolve the graph by name or id (names are expected to be unique).
        with requests.Session() as session:
            graphs = self.client.http_get("/api/graph", session=session)
        matches = [
            g for g in graphs if g.get("name") == graph_name or g.get("id") == graph_name
        ]
        if not matches:
            raise Exception(f"No graph named (or with id) '{graph_name}' found.")
        if len(matches) > 1:
            raise Exception(
                f"Multiple graphs named '{graph_name}'; names are not unique — pass the graph id."
            )
        graph_id = matches[0]["id"]

        # Enumerate the graph's file-documents (documentId -> name) from its reconciled subjects.
        with requests.Session() as session:
            subjects_graph = self.client.http_get(
                f"/api/graph/{graph_id}/subjects-graph", session=session
            )
        documents: dict = {}
        for subject in subjects_graph.get("subjects", []):
            for entity in subject.get("entities", []):
                file_id, name = entity.get("fileId"), entity.get("fileName")
                if file_id and name:
                    documents.setdefault(file_id, name)
        if not documents:
            raise Exception(
                "Graph has no documents with reconciled subjects — reconcile the graph first."
            )

        os.makedirs(output_dir, exist_ok=True)
        # Index local originals by their path RELATIVE to files_dir. An uploader typically names each
        # document by that relative path (e.g. name=os.path.relpath(file, files_dir)), so files in
        # nested folders round-trip. Hidden files/dirs are ignored.
        local_by_relpath: dict = {}
        for dirpath, dirnames, filenames in os.walk(files_dir):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                full_path = os.path.join(dirpath, filename)
                local_by_relpath[os.path.relpath(full_path, files_dir)] = full_path

        written: List[str] = []
        for document_id, name in sorted(documents.items(), key=lambda kv: kv[1].lower()):
            original_path = local_by_relpath.get(name)
            if original_path is None:
                warn(f"Skipping '{name}': no local original under '{files_dir}' to re-supply.")
                continue

            with open(original_path, "rb") as handle:
                try:
                    content = self.client.http_post_download_file(
                        f"/api/graph/{graph_id}/documents/{document_id}/redact-pdf",
                        files={"file": (os.path.basename(name), handle, "application/pdf")},
                    )
                except requests.exceptions.HTTPError as err:
                    if err.response is not None and err.response.status_code == 404:
                        warn(
                            f"Skipping '{name}': not a redactable file document "
                            "(no stored PDF geometry)."
                        )
                        continue
                    raise

            # Mirror the document's relative path under output_dir, suffixed .redacted.pdf.
            out_path = os.path.join(output_dir, f"{os.path.splitext(name)[0]}.redacted.pdf")
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as out_file:
                out_file.write(content)
            written.append(out_path)

        return written
