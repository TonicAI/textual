from __future__ import annotations

import io
import json
import os
import time
import uuid
from typing import Callable, List, Optional

import requests

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.subject_graph import CollectionSubjectGraph
from tonic_textual.classes.tonic_exception import GraphRenderBatchError

# Terminal reconcile / synthesize job states. Queued and Running are the only non-terminal
# states, so anything else ends the wait loop (Completed is success; the rest are failures).
_TERMINAL_JOB_STATES = {"Completed", "Failed", "Canceled", "Skipped"}
MAX_RENDER_BATCH_ITEMS = 500
MAX_RENDER_BATCH_UTF16_CODE_UNITS = 4_000_000


def _utf16_code_units(value: str) -> int:
    """Return the character count used by .NET ``string.Length``."""

    return len(value.encode("utf-16-le", errors="surrogatepass")) // 2


def _validate_render_seed(seed: Optional[int]) -> None:
    if seed is None:
        return
    if type(seed) is not int or not -(2**31) <= seed <= 2**31 - 1:
        raise ValueError("random_seed must be a signed 32-bit integer")


def _response_error_code(response) -> Optional[str]:
    try:
        payload = response.json()
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    for key in ("code", "errorCode", "error_code", "type"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    error = payload.get("error")
    if isinstance(error, dict):
        for key in ("code", "errorCode", "error_code", "type"):
            value = error.get(key)
            if isinstance(value, str) and value:
                return value
    return None


class SubjectGraph:
    """A standalone subject graph built by streaming text in, reconciling, and synthesizing.

    A ``SubjectGraph`` is the dataset-free unit of work for the ``/api/graph`` streaming API. Unlike
    :class:`~tonic_textual.classes.subject_collection.SubjectCollection`, it does not own a general
    file collection: text is supplied again at render time, while standalone PDFs are retained in
    private object storage so their V5-styled output can be rendered by document id. After ingest,
    :meth:`reconcile` groups mentions into canonical subjects and :meth:`synthesize` fills the
    synthetic bundles over the whole graph.

    The subject / relationship surface (:meth:`create_subject`, :meth:`add_relationship`,
    :meth:`merge_subjects`, :meth:`delete_relationship`, :meth:`get_subject_graph`) mirrors
    ``SubjectCollection`` one-for-one, hitting ``/api/graph/{id}/...`` instead of
    ``/api/dataset/{id}/...``, so the graph can be inspected and enriched between reconcile and
    synthesize exactly like a collection.
    """

    def __init__(self, client: HttpClient, id: str, name: Optional[str] = None):
        self.client = client
        self.id = id
        self.name = name

    # ------------------------------------------------------------------
    # Build phase — synchronous, jobless ingest
    # ------------------------------------------------------------------
    def add_text(
        self,
        text: str,
        document_id: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Ingests a piece of raw text into the graph as a document (streaming build phase).

        This is SYNCHRONOUS and creates no job: the server detects entities in ``text`` and folds
        their mentions into the graph before the call returns. Re-posting with the same
        ``document_id`` replaces that document's mentions, so a document can be updated in place.

        Parameters
        ----------
        text : str
            The raw text to ingest. Detected and folded into the graph on this call; grouped into
            subjects on the next :meth:`reconcile`.
        document_id : Optional[str]
            Reuse an existing document id to replace its mentions. When omitted, the server assigns
            a new id (returned).
        name : Optional[str]
            Optional human-readable document name.

        Returns
        -------
        str
            The document id — pass it to :meth:`render_document` after :meth:`synthesize`.

        Examples
        --------
        >>> doc_id = graph.add_text("Meg, did Sheryl at Hoosier Endo email you?")
        >>> graph.reconcile(wait=True); graph.synthesize(wait=True)
        >>> graph.render_document(doc_id, text="Meg, did Sheryl at Hoosier Endo email you?")
        """
        body: dict = {"text": text}
        if document_id is not None:
            body["documentId"] = document_id
        if name is not None:
            body["name"] = name
        if metadata is not None:
            # The endpoint takes metadata as a JSON string (stored on the GraphDocument and consumed
            # by reconcile's metadata policy).
            body["metadata"] = json.dumps(metadata)
        response = self.client.http_post(f"/api/graph/{self.id}/text", data=body)
        if isinstance(response, dict):
            return response.get("documentId", "")
        return response

    def add_texts(self, documents: List[dict]) -> List[str]:
        """Bulk-ingests many documents in ONE request (synchronous, no job).

        All texts are sent to the NER model TOGETHER (batched server-side), never one at a time — far
        faster than calling :meth:`add_text` per document. Each item is a dict with ``text`` (required)
        and optional ``document_id``, ``name``, and ``metadata`` (a DocumentContext dict). Re-posting an
        existing ``document_id`` replaces that document's mentions.

        Returns the document ids in the same order as ``documents``.
        """
        payload: List[dict] = []
        for d in documents:
            item: dict = {"text": d["text"]}
            if d.get("document_id") is not None:
                item["documentId"] = d["document_id"]
            if d.get("name") is not None:
                item["name"] = d["name"]
            if d.get("metadata") is not None:
                item["metadata"] = json.dumps(d["metadata"])
            payload.append(item)
        response = self.client.http_post(
            f"/api/graph/{self.id}/bulk_text", data={"documents": payload}
        )
        docs = response.get("documents", []) if isinstance(response, dict) else []
        return [doc.get("documentId", "") for doc in docs]

    def add_pdf(
        self,
        file_path: Optional[str] = None,
        file: Optional[io.IOBase] = None,
        name: Optional[str] = None,
        document_id: Optional[str] = None,
        wait: bool = True,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
    ) -> str:
        """Ingests a PDF into the graph as a BACKGROUND job (the "PDF content informs the graph" path).

        Unlike :meth:`add_text`, PDF ingest is asynchronous: the server OCR-parses the PDF, detects
        PII, detects V5 styles for the retained PII mentions (including later enrichment), and
        persists the source in private object storage together with per-page mentions and geometry.
        This posts the bytes to
        ``/api/graph/{id}/pdf`` and, when ``wait`` is True, blocks until the ingest job finishes.
        Re-posting the same ``document_id`` replaces the source, mentions, geometry, and styles.

        Parameters
        ----------
        file_path : Optional[str]
            Path to the PDF to upload. Provide this OR ``file`` (not both).
        file : Optional[io.IOBase]
            An open binary file-like object for the PDF. When used, ``name`` is recommended.
        name : Optional[str]
            Human-readable document name (defaults to the file's base name).
        document_id : Optional[str]
            Reuse an existing document id to replace its mentions. When omitted, a new id is
            generated client-side (and returned) so the ingest job can be polled by document.
        wait : bool
            When True (default), block until the ingest job reaches a terminal state (or times out).
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.

        Returns
        -------
        str
            The document id — pass it to :meth:`render_document` after :meth:`reconcile` /
            :meth:`synthesize`.

        Raises
        ------
        ValueError
            If neither or both of ``file_path`` / ``file`` are provided.
        RuntimeError
            When ``wait`` is True and the ingest job ends in a non-``Completed`` state.
        TimeoutError
            When ``wait`` is True and the job does not finish within ``timeout_seconds``.

        Examples
        --------
        >>> doc_id = graph.add_pdf("contract.pdf")   # blocks until OCR + detection finish
        >>> graph.reconcile(wait=True); graph.synthesize(wait=True)
        """
        if (file_path is None) == (file is None):
            raise ValueError("Provide exactly one of file_path or file.")

        # Generate the document id client-side when not supplied so we can poll this exact document's
        # ingest job (the status endpoint is keyed by document id, and the JobModel carries no doc id).
        doc_id = document_id or uuid.uuid4().hex
        doc_name = name or (os.path.basename(file_path) if file_path else doc_id)

        f = open(file_path, "rb") if file_path is not None else file
        try:
            files = {"file": (doc_name, f, "application/pdf")}
            job = self.client.http_post(
                f"/api/graph/{self.id}/pdf",
                params={"documentId": doc_id, "name": doc_name},
                files=files,
            )
        finally:
            if file_path is not None:
                f.close()

        if wait:
            self._wait_for_job(
                job,
                lambda: self.get_pdf_ingest_status(doc_id),
                "pdf ingest",
                timeout_seconds,
                poll_interval_seconds,
            )
        return doc_id

    def get_pdf_ingest_status(self, document_id: str) -> Optional[dict]:
        """Returns the latest PDF-ingest job for ``document_id`` in this graph, or ``None`` if never
        ingested. The returned dict mirrors the job model (``id``, ``status``, ...); ``status`` is one
        of ``Queued`` / ``Running`` / ``Completed`` / ``Failed`` / ``Canceled`` / ``Skipped``.
        """
        with requests.Session() as session:
            return self.client.http_get(
                f"/api/graph/{self.id}/pdf-status",
                params={"documentId": document_id},
                session=session,
            )

    # ------------------------------------------------------------------
    # Reconcile / synthesize — whole-graph jobs
    # ------------------------------------------------------------------
    def reconcile(
        self,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
        linking_profile: Optional[dict] = None,
    ) -> None:
        """Runs batch reconciliation over the whole graph, grouping mentions into subjects.

        Reconciliation is decoupled from ingest: :meth:`add_text` folds in mentions, but subjects
        are not (re)built until you call this. It looks at every document's mentions at once, groups
        them into canonical subjects (order-independently), and replaces the graph's subject graph
        atomically WITHOUT synthetic values, so the graph can be inspected and enriched before
        :meth:`synthesize`. Call it after streaming in text — and again after adding more.

        Parameters
        ----------
        wait : bool
            When True, block until the reconcile job reaches a terminal state (or times out)
            instead of returning as soon as it is queued.
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.
        linking_profile : Optional[dict]
            A declarative linking profile describing how subjects are clustered, merged, related, and
            synthesized. When omitted (None), the server reconciles with its built-in default profile,
            so existing callers are unaffected. Invalid profiles are rejected by the server with a 400.

        Raises
        ------
        RuntimeError
            Raised when ``wait`` is True and the reconcile job ends in a non-``Completed`` state.
        TimeoutError
            Raised when ``wait`` is True and the job does not finish within ``timeout_seconds``.

        Examples
        --------
        >>> graph.reconcile(wait=True)
        >>> print(len(graph.get_subject_graph().subjects))
        """
        body = {"linkingProfile": linking_profile} if linking_profile is not None else {}
        job = self.client.http_post(f"/api/graph/{self.id}/reconcile", data=body)
        if not wait:
            return
        self._wait_for_job(
            job, self.get_reconcile_status, "reconcile", timeout_seconds, poll_interval_seconds
        )

    def add_to_allowlist(self, label: str, values: List[str]) -> None:
        """Force-detect ``values`` as ``label`` on every subsequent (re-)ingest.

        Each value becomes a case-insensitive whole-token regex that is added to the graph's allow list
        for ``label`` — a custom recognizer that catches entities the model misses. It is applied at the
        shared detection seam that BOTH text (:meth:`add_text`) and PDF (:meth:`add_pdf`) ingest go
        through, so it is source-agnostic: it takes effect for every document you (re-)ingest afterward.
        Existing mentions are unchanged until their document is re-ingested; re-``reconcile`` after to fold
        the newly-detected mentions into subjects.

        The canonical use is guaranteeing a known organization name is always detected (and thus redacted
        / synthesized): ``graph.add_to_allowlist("ORGANIZATION", ["mesha"])``.

        Parameters
        ----------
        label : str
            The entity label to force-detect matches as, e.g. ``"ORGANIZATION"``.
        values : List[str]
            The surface values to force-detect (e.g. every distinct spelling of the org).

        Examples
        --------
        >>> graph.add_to_allowlist("ORGANIZATION", ["mesha", "Mesha"])
        """
        self.client.http_post(
            f"/api/graph/{self.id}/allowlist", data={"label": label, "values": values}
        )

    def get_reconcile_status(self) -> Optional[dict]:
        """Returns the latest reconcile job for the graph, or ``None`` if never reconciled.

        The returned dict mirrors the job model (``id``, ``status``, ...); ``status`` is one of
        ``Queued`` / ``Running`` / ``Completed`` / ``Failed`` / ``Canceled`` / ``Skipped``.
        """
        with requests.Session() as session:
            return self.client.http_get(
                f"/api/graph/{self.id}/reconcile-status", session=session
            )

    def synthesize(
        self,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        """Runs phase 2 — synthesis — over the already-reconciled graph, freezing it.

        :meth:`reconcile` only groups mentions into subjects; this generates the coherent synthetic
        bundles over that graph (honoring any enrichments added in between) and atomically
        re-persists it. Requires a reconciled graph to exist (call :meth:`reconcile` first). After
        this, :meth:`render_document` can splice the frozen synthetic values into any ingested
        document.

        Parameters
        ----------
        wait : bool
            When True, block until the synthesis job reaches a terminal state (or times out).
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.

        Raises
        ------
        RuntimeError
            Raised when ``wait`` is True and the synthesis job ends in a non-``Completed`` state.
        TimeoutError
            Raised when ``wait`` is True and the job does not finish within ``timeout_seconds``.

        Examples
        --------
        >>> graph.reconcile(wait=True)
        >>> # ... optionally enrich the graph here ...
        >>> graph.synthesize(wait=True)
        """
        job = self.client.http_post(f"/api/graph/{self.id}/synthesize")
        if not wait:
            return
        self._wait_for_job(
            job, self.get_synthesize_status, "synthesize", timeout_seconds, poll_interval_seconds
        )

    def get_synthesize_status(self) -> Optional[dict]:
        """Returns the latest synthesize job for the graph, or ``None`` if never synthesized.

        The returned dict mirrors the job model (``id``, ``status``, ...); ``status`` is one of
        ``Queued`` / ``Running`` / ``Completed`` / ``Failed`` / ``Canceled`` / ``Skipped``.
        """
        with requests.Session() as session:
            return self.client.http_get(
                f"/api/graph/{self.id}/synthesize-status", session=session
            )

    def _wait_for_job(
        self,
        job,
        status_fn: Callable[[], Optional[dict]],
        label: str,
        timeout_seconds: float,
        poll_interval_seconds: float,
    ) -> None:
        """Polls ``status_fn`` until the started ``job`` reaches a terminal state.

        Mirrors ``SubjectCollection.synthesize``'s wait loop: matches the job we started (by id) so
        a stale prior run's terminal status can't end the wait early, raises on a non-``Completed``
        terminal state, and raises ``TimeoutError`` past the deadline.
        """
        job_id = job.get("id") if isinstance(job, dict) else None
        deadline = time.monotonic() + timeout_seconds
        last_report = None
        while True:
            status = status_fn()
            state = status.get("status") if status else None
            current = status and (job_id is None or status.get("id") == job_id)

            # Log progress so a long-running job shows movement instead of a silent wait. `progress`
            # is a 0–100 percentage (null until the server's first update) and `tasks` is the list of
            # per-phase progress rows the server persists (each with an `action`, `stepsCompleted`, and
            # `totalSteps`); we render them as a compact "phase steps/total" string and print only when
            # the rounded percentage, the per-phase string, or the state changes, so the log advances
            # without spamming.
            if current:
                pct = status.get("progress")
                tasks = status.get("tasks") or []
                phases = "; ".join(
                    f"{t['action']} {t['stepsCompleted']}/{t['totalSteps']}"
                    for t in tasks
                    if t.get("totalSteps")
                )
                overall = None if pct is None else round(pct)
                report = (state, overall, phases)
                if report != last_report:
                    last_report = report
                    pct_str = f"{overall}%" if overall is not None else "..."
                    phases_str = f" [{phases}]" if phases else ""
                    print(f"  {label}: {pct_str}{phases_str} ({state})", flush=True)

            if current and state in _TERMINAL_JOB_STATES:
                if state != "Completed":
                    raise RuntimeError(
                        f"Graph {label} for '{self.name or self.id}' ended with status '{state}'."
                    )
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Graph {label} for '{self.name or self.id}' did not finish within "
                    f"{timeout_seconds} seconds."
                )
            time.sleep(poll_interval_seconds)

    # ------------------------------------------------------------------
    # Read-back
    # ------------------------------------------------------------------
    def get_subject_graph(self) -> CollectionSubjectGraph:
        """Returns every subject in the graph and how they relate.

        Same shape as ``SubjectCollection.get_subject_graph`` — subjects may span multiple ingested
        documents (cross-document linking merges mentions of the same identity), with collection-
        level stats. Call this after :meth:`reconcile` has completed.

        Returns
        -------
        CollectionSubjectGraph

        Examples
        --------
        >>> graph.reconcile(wait=True)
        >>> print(graph.get_subject_graph().describe())
        """
        with requests.Session() as session:
            response = self.client.http_get(
                f"/api/graph/{self.id}/subjects-graph", session=session
            )
        return CollectionSubjectGraph.from_dict(response, collection_name=self.name)

    def render_document(
        self,
        document_id: str,
        text: str,
        random_seed: Optional[int] = None,
    ) -> str:
        """Renders one document's synthetic text from the FROZEN graph (after :meth:`synthesize`).

        Splices the persisted graph's synthetic values into ``text`` at the document's stored entity
        offsets. A graph keeps no document content, so ``text`` is REQUIRED ("discard mode") — it
        must be byte-identical to what was ingested via :meth:`add_text`, or the offset splices
        misalign. Because this reads from the persisted graph, its output is consistent with every
        other document's for cross-document consistency.

        Parameters
        ----------
        document_id : str
            The document id returned by :meth:`add_text`.
        text : str
            Byte-identical original text to splice the synthetic values into.
        random_seed : Optional[int]
            Optional seed override (sent as the ``textual-random-seed`` header, same semantics as
            ``CollectionFile.download``) so entities not covered by the graph render
            deterministically.

        Returns
        -------
        str
            The document's synthetic text.

        Examples
        --------
        >>> doc_id = graph.add_text("Meg, did Sheryl at Hoosier Endo email you?")
        >>> graph.reconcile(wait=True); graph.synthesize(wait=True)
        >>> graph.render_document(doc_id, text="Meg, did Sheryl at Hoosier Endo email you?")
        """
        response = self._render(document_id, text, random_seed)
        if isinstance(response, dict):
            return response.get("synthetic", "")
        return response

    def render_document_detailed(
        self,
        document_id: str,
        text: str,
        random_seed: Optional[int] = None,
    ) -> dict:
        """Like :meth:`render_document`, but returns the full response: ``{"documentId", "synthetic",
        "entities"}``, where ``entities`` is the per-detection mapping (``start``/``end``/``label``/
        ``text``/``newText``) actually applied to the text — for callers that need span-level results
        (e.g. benchmarking), not just the rendered string.
        """
        response = self._render(document_id, text, random_seed)
        return response if isinstance(response, dict) else {"synthetic": response, "entities": []}

    def render_documents_batch(
        self,
        items: List[dict],
        random_seed: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ) -> dict:
        """Render multiple generic documents in one projection request.

        ``items`` must contain dictionaries with ``documentId`` and ``text`` keys. The server may
        return item-level failures inside an otherwise successful response; those are returned to the
        caller unchanged. A request-level failure raises :class:`GraphRenderBatchError` and retains
        the originating HTTP response for callers that need its structured conflict details.

        The method deliberately sends one request, rather than splitting an arbitrary iterable. The
        caller owns batching policy and can preserve its own document-to-output association while this
        SDK method enforces the Graph request limits and wire contract.

        Parameters
        ----------
        items : List[dict]
            Generic render items in the desired association order. Each item has ``documentId`` and
            exact original ``text``; an optional ``seed`` is accepted for compatibility with the API.
        random_seed : Optional[int]
            One seed for the request. When supplied, it is applied to every item and the request
            header. Any item-level seed must match it.
        timeout_seconds : Optional[int]
            Optional HTTP request timeout.
        """
        if not isinstance(items, (list, tuple)):
            raise TypeError("items must be a list or tuple")
        if not items:
            raise ValueError("items must not be empty")
        if len(items) > MAX_RENDER_BATCH_ITEMS:
            raise ValueError(
                f"render batch contains {len(items)} items; maximum is {MAX_RENDER_BATCH_ITEMS}"
            )

        _validate_render_seed(random_seed)
        normalized_items = []
        item_seeds = []
        total_units = 0
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError(f"render batch item {index} must be a dictionary")
            document_id = item.get("documentId")
            text = item.get("text")
            if not isinstance(document_id, str) or not document_id.strip():
                raise ValueError(f"render batch item {index} requires documentId")
            if not isinstance(text, str):
                raise ValueError(f"render batch item {index} requires text")

            total_units += _utf16_code_units(text)
            if total_units > MAX_RENDER_BATCH_UTF16_CODE_UNITS:
                raise ValueError(
                    "render batch exceeds the maximum of "
                    f"{MAX_RENDER_BATCH_UTF16_CODE_UNITS} UTF-16 code units"
                )

            item_seed = item.get("seed")
            if item_seed is not None:
                _validate_render_seed(item_seed)
                item_seeds.append(item_seed)
            normalized = {"documentId": document_id, "text": text}
            normalized_items.append(normalized)

        if item_seeds and len(set(item_seeds)) != 1:
            raise ValueError("all render batch item seeds must be identical")
        if item_seeds and random_seed is not None and item_seeds[0] != random_seed:
            raise ValueError("render batch item seed must match random_seed")
        effective_seed = random_seed if random_seed is not None else (
            item_seeds[0] if item_seeds else None
        )
        if effective_seed is not None:
            for item in normalized_items:
                item["seed"] = effective_seed

        headers = (
            {"textual-random-seed": str(effective_seed)}
            if effective_seed is not None
            else {}
        )
        response = self.client.http_post_raw(
            f"/api/graph/{self.id}/documents/render-batch",
            data={"items": normalized_items},
            additional_headers=headers,
            timeout_seconds=timeout_seconds,
        )

        if not 200 <= response.status_code < 300:
            raise GraphRenderBatchError(
                f"Graph render batch failed with HTTP {response.status_code}",
                response=response,
                code=_response_error_code(response),
            )
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise GraphRenderBatchError(
                "Graph render batch returned a non-JSON response", response=response
            ) from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            raise GraphRenderBatchError(
                "Graph render batch returned an invalid response shape", response=response
            )

        requested_ids = [item["documentId"] for item in normalized_items]
        response_items = payload["items"]
        by_id = {}
        for index, item in enumerate(response_items):
            if not isinstance(item, dict) or not isinstance(item.get("documentId"), str):
                raise GraphRenderBatchError(
                    f"Graph render batch item {index} has no documentId", response=response
                )
            document_id = item["documentId"]
            if document_id in by_id:
                raise GraphRenderBatchError(
                    f"Graph render batch returned duplicate documentId {document_id!r}",
                    response=response,
                )
            by_id[document_id] = item
        if set(by_id) != set(requested_ids) or len(by_id) != len(requested_ids):
            raise GraphRenderBatchError(
                "Graph render batch response does not match the requested document ids",
                response=response,
            )

        # The API promises request order, but normalizing here makes association deterministic even if
        # a compatible server returns items in a different order.
        normalized_payload = dict(payload)
        normalized_payload["items"] = [by_id[document_id] for document_id in requested_ids]
        return normalized_payload

    def render_pdf(
        self,
        document_id: str,
        random_seed: Optional[int] = None,
    ) -> bytes:
        """Renders a retained standalone PDF from the frozen graph.

        The original PDF was retained by :meth:`add_pdf`, so callers provide only its document id.
        The server resolves the graph-wide synthetic values, applies their stored V5 font and placement
        data, and returns the synthesized PDF bytes. Call :meth:`reconcile` and :meth:`synthesize`
        first.

        Parameters
        ----------
        document_id : str
            The document id returned by :meth:`add_pdf`.
        random_seed : Optional[int]
            Optional seed override for any server-side fallback generation.

        Returns
        -------
        bytes
            The synthesized PDF.
        """
        headers = (
            {"textual-random-seed": str(random_seed)} if random_seed is not None else {}
        )
        with requests.Session() as session:
            return self.client.http_get_file(
                f"/api/graph/{self.id}/documents/{document_id}/render-pdf",
                session=session,
                additional_headers=headers,
            )

    def _render(self, document_id: str, text: str, random_seed: Optional[int]):
        headers = (
            {"textual-random-seed": str(random_seed)} if random_seed is not None else {}
        )
        return self.client.http_post(
            f"/api/graph/{self.id}/documents/{document_id}/render",
            data={"text": text},
            additional_headers=headers,
        )

    def redact(self, text: str) -> str:
        """Stateless "redacted linking": replace each detected entity in ``text`` with a STRUCTURAL
        label projected from this graph — ``PERSON1``, ``PERSON1_EMAIL``, ``ORG1`` — or ``{TYPE}_UNK``
        when the entity isn't in the graph. Read-only: does NOT mutate the graph, and ``text`` need not
        have been ingested.

        Unlike :meth:`render_document` (which produces realistic synthetic values for one stored,
        synthesized document), this produces graph-structure labels for ARBITRARY text and needs no
        ``document_id`` — resolution is by entity value against the graph's subjects. Text byte-identical
        to a previously-ingested, reconciled document is resolved from that document's stored linkage
        (exact, resolves even ambiguous names); novel text is detected fresh and resolved by surface
        with hard-key-anchored disambiguation.

        Parameters
        ----------
        text : str
            The text to redact.

        Returns
        -------
        str
            The text with entities replaced by structural labels.

        Examples
        --------
        >>> graph.add_text("Adam works at Tonic. His email is adam@tonic.ai.")
        >>> graph.reconcile(wait=True)
        >>> graph.redact("Adam works at Tonic. His email is adam@tonic.ai.")
        'PERSON1 works at ORG1. His email is PERSON1_EMAIL'
        """
        response = self._redact(text)
        if isinstance(response, dict):
            return response.get("redactedText", "")
        return response

    def redact_detailed(self, text: str) -> dict:
        """Like :meth:`redact`, but returns the full response: ``{"redactedText", "entities",
        "matchedDocumentId"}``. ``entities`` is the per-detection mapping (``start``/``end``/``label``/
        ``text``/``newText``) applied to the text; ``matchedDocumentId`` is set when the input matched a
        previously-ingested reconciled document by content checksum (resolved from its stored linkage),
        else null.
        """
        response = self._redact(text)
        return (
            response
            if isinstance(response, dict)
            else {"redactedText": response, "entities": [], "matchedDocumentId": None}
        )

    def _redact(self, text: str):
        return self.client.http_post(
            f"/api/graph/{self.id}/redact",
            data={"text": text},
        )

    def synthesize_text(self, text: str) -> str:
        """Stateless REALISTIC synthesis: replace each detected entity in ``text`` with the frozen
        synthetic value this graph carries for its subject — fake-but-plausible and consistent with
        every other document. The realistic twin of :meth:`redact` (which emits structural labels).

        Unlike :meth:`render_document` (which renders one stored document by id), this synthesizes
        ARBITRARY text and needs no ``document_id``. Text byte-identical to a previously-ingested,
        reconciled document is rendered from that document's stored linkage (Type 2, highest fidelity —
        resolves even ambiguous names); novel text is detected fresh and resolved by surface with
        hard-key-anchored disambiguation (Type 1), with anything unresolved rendered by the per-entity
        generator (a realistic value, not a graph identity).

        Requires the graph to be SYNTHESIZED (call :meth:`synthesize` first). Raises if the graph's
        bundles were never generated or went stale after a later ingest/reconcile/edit — there is no
        silent fallback. For structural labels instead (no synthesis needed), use :meth:`redact`.

        Parameters
        ----------
        text : str
            The text to synthesize.

        Returns
        -------
        str
            The text with entities replaced by realistic synthetic values.

        Examples
        --------
        >>> graph.reconcile(wait=True)
        >>> graph.synthesize(wait=True)
        >>> graph.synthesize_text("Adam works at Tonic. His email is adam@tonic.ai.")
        'Marcus works at Ravenline. His email is marcus.bellweather@ravenline.io.'
        """
        response = self._synthesize_text(text)
        if isinstance(response, dict):
            return response.get("syntheticText", "")
        return response

    def synthesize_text_detailed(self, text: str) -> dict:
        """Like :meth:`synthesize_text`, but returns the full response: ``{"syntheticText", "entities",
        "matchedDocumentId"}``. ``entities`` is the per-detection mapping (``start``/``end``/``label``/
        ``text``/``newText``) applied to the text; ``matchedDocumentId`` is set when the input matched a
        previously-ingested reconciled document by content checksum (rendered from stored linkage), else
        null.
        """
        response = self._synthesize_text(text)
        return (
            response
            if isinstance(response, dict)
            else {"syntheticText": response, "entities": [], "matchedDocumentId": None}
        )

    def _synthesize_text(self, text: str):
        return self.client.http_post(
            f"/api/graph/{self.id}/synthesize-text",
            data={"text": text},
        )

    # ------------------------------------------------------------------
    # Enrichment — same request bodies as SubjectCollection
    # ------------------------------------------------------------------
    def create_subject(
        self,
        identity_type: str,
        named_entity_ids: Optional[List[str]] = None,
    ) -> dict:
        """Creates a new subject in the reconciled graph (enrichment step, before :meth:`synthesize`).

        Parameters
        ----------
        identity_type : str
            The subject's identity type (e.g. ``"Person"``, ``"Organization"``, ``"SlackUsername"``).
        named_entity_ids : Optional[List[str]]
            Ids of existing detected entities in the graph to group under the new subject.

        Returns
        -------
        dict
            ``{"id": ..., "identityType": ...}`` for the created subject.
        """
        body = {"identityType": identity_type, "namedEntityIds": named_entity_ids or []}
        return self.client.http_post(f"/api/graph/{self.id}/subjects", data=body)

    def add_relationship(
        self,
        left_subject_id: str,
        right_subject_id: str,
        relationship_type: str,
        confidence: Optional[float] = None,
    ) -> dict:
        """Adds a directed relationship edge between two subjects (enrichment step, before synthesize).

        Parameters
        ----------
        left_subject_id, right_subject_id : str
            The edge endpoints (both must be subjects of this graph).
        relationship_type : str
            The edge type, e.g. ``"OwnedBy"``, ``"HostedAt"``, ``"WorksAt"``, ``"BrandOf"``.
        confidence : Optional[float]
            Confidence in [0, 1]; defaults to 1.0 for a manual assertion.

        Returns
        -------
        dict
            ``{"id": ...}`` for the created relationship.
        """
        body = {
            "leftSubjectId": left_subject_id,
            "rightSubjectId": right_subject_id,
            "type": relationship_type,
        }
        if confidence is not None:
            body["confidence"] = confidence
        return self.client.http_post(f"/api/graph/{self.id}/relationships", data=body)

    def merge_subjects(self, survivor_subject_id: str, loser_subject_id: str) -> None:
        """Merges ``loser_subject_id`` into ``survivor_subject_id`` (enrichment step, before synthesize).

        The loser's links and relationships move to the survivor (self-loops and duplicates dropped),
        then the loser subject is deleted.
        """
        body = {
            "survivorSubjectId": survivor_subject_id,
            "loserSubjectId": loser_subject_id,
        }
        self.client.http_post(f"/api/graph/{self.id}/subjects/merge", data=body)

    def split_subject(self, subject_id: str, named_entity_ids: List[str]) -> dict:
        """Splits a subset of a subject's mentions into a NEW subject of the same type (over-merge fix;
        enrichment step, before :meth:`synthesize`).

        The listed mentions are MOVED into a new subject — never orphaned — so they still synthesize
        consistently as their own identity. Must be a strict, non-empty subset (leave at least one
        mention on the source). Re-synthesize afterward so both subjects get fresh, consistent bundles.

        Parameters
        ----------
        subject_id : str
            The source (over-merged) subject to split.
        named_entity_ids : List[str]
            Ids of the source's mentions (``entity_id`` from the subject graph) to move into a new subject.

        Returns
        -------
        dict
            ``{"id": ..., "identityType": ...}`` for the newly created subject.
        """
        body = {"namedEntityIds": named_entity_ids}
        return self.client.http_post(f"/api/graph/{self.id}/subjects/{subject_id}/split", data=body)

    def delete_relationship(self, relationship_id: str) -> None:
        """Deletes a single relationship edge (enrichment step, before :meth:`synthesize`)."""
        self.client.http_delete(f"/api/graph/{self.id}/relationships/{relationship_id}")

    def delete(self) -> None:
        """Deletes this graph and everything in it."""
        self.client.http_delete(f"/api/graph/{self.id}")
