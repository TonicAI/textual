from __future__ import annotations

import io
import time
import uuid
from typing import Iterator, List, Optional

import requests

from tonic_textual.classes.collection_file import CollectionFile
from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.file_review import FileReview
from tonic_textual.classes.generator_metadata.name_generator_metadata import (
    NameGeneratorMetadata,
)
from tonic_textual.classes.subject_graph import CollectionSubjectGraph
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import PiiType

# The NER labels the subject linker groups into subjects, mirroring the backend's
# SubjectLinkingPiiTypes. Person attributes + organization + the identifier identity types
# (email / phone / url / address).
SUBJECT_LINKING_ENTITY_LABELS: List[str] = [
    # Person
    "NAME_GIVEN",
    "NAME_FAMILY",
    "PERSON",
    "US_SSN",
    "US_PASSPORT",
    "US_ITIN",
    "DOB",
    "PERSON_AGE",
    # Organization
    "ORGANIZATION",
    # Email / Phone / Url
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "URL",
    # Address
    "LOCATION_ADDRESS",
    "LOCATION_CITY",
    "LOCATION_STATE",
    "LOCATION_ZIP",
    "LOCATION",
]


class SubjectCollection(Dataset):
    """A collection of files that Tonic Textual scans, groups into subjects, and synthesizes.

    A subject collection is the unit of work for subject linking: you add files to it, Textual
    detects PII across those files, groups the detected entities into subjects (people,
    organizations, and the identifiers that belong to them), and links related subjects together.

    ``SubjectCollection`` inherits the full file-management surface of its parent (adding,
    listing, and removing files), so those capabilities work unchanged. Subject-specific
    methods (listing subjects, inspecting how they link, etc.) are layered on over time.
    """

    @classmethod
    def _from_dataset(cls, dataset: Dataset) -> "SubjectCollection":
        """Re-type a freshly built :class:`Dataset` as a :class:`SubjectCollection`.

        The dataset service constructs a new ``Dataset`` instance per call, so reassigning
        ``__class__`` is safe — it has no shared-instance side effects and preserves every
        populated attribute without mirroring ``Dataset``'s constructor.
        """
        dataset.__class__ = cls
        return dataset  # type: ignore[return-value]

    def add_file(
        self,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None,
        file: Optional[io.IOBase] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[CollectionFile]:
        """Adds a file to the subject collection and uploads it.

        Provide either ``file_path`` to upload a file from disk, or ``file`` (a byte stream)
        together with ``file_name``. Once uploaded, Tonic Textual scans the file and folds its
        detected entities into the collection's subjects.

        Parameters
        ----------
        file_path : Optional[str]
            The absolute path of the file to upload. If specified, you cannot also provide
            ``file``.
        file_name : Optional[str]
            The name to store the file under. Optional when uploading via ``file_path``
            (defaults to the path's base name); required when uploading via ``file``.
        file : Optional[io.IOBase]
            The bytes of a file to upload. If specified, you must also provide ``file_name``,
            and you cannot use ``file_path`` in the same call.

        Returns
        -------
        Optional[CollectionFile]
            The uploaded file.

        Raises
        ------
        BadArgumentsException
            Raised if the file arguments are inconsistent (e.g. both ``file_path`` and
            ``file``, or ``file`` without ``file_name``).
        DatasetFileMatchesExistingFile
            Raised if the file content matches a file already in the collection.
        """
        uploaded = super().add_file(
            file_path=file_path, file_name=file_name, file=file, metadata=metadata
        )

        # The upload rebuilds the file list as DatasetFiles; re-type them (and the returned
        # file) so the collection's surface stays dressed in collection terms.
        self.files = [CollectionFile._from_dataset_file(f) for f in self.files]

        if uploaded is None:
            return None
        return CollectionFile._from_dataset_file(uploaded)

    def add_text(
        self,
        text: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[CollectionFile]:
        """Adds a piece of raw text to the collection as a document (streaming build phase).

        Convenience over ``add_file``: uploads ``text`` as a UTF-8 ``.txt`` document so its detected
        entities fold into the collection's subjects — without you managing a file on disk. The
        returned file's ``id`` is the document id to pass to ``render_document`` after ``synthesize``.

        Parameters
        ----------
        text : str
            The raw text to ingest. Detected on upload; added to the subject graph on the next
            ``link()``.
        name : Optional[str]
            Document name. A ``.txt`` extension is enforced so the text is processed as raw text;
            defaults to a generated unique ``.txt`` name.
        metadata : Optional[dict]
            Optional per-document metadata (same as ``add_file``).

        Returns
        -------
        Optional[CollectionFile]
            The uploaded document; its ``.id`` is the document id.

        Examples
        --------
        >>> doc = collection.add_text("Meg, did Sheryl at Hoosier Endo email you?")
        >>> collection.link(wait=True); collection.synthesize(wait=True)
        >>> collection.render_document(doc.id)
        """
        if name is None:
            name = f"text-{uuid.uuid4().hex}.txt"
        elif not name.lower().endswith(".txt"):
            name = f"{name}.txt"
        buffer = io.BytesIO(text.encode("utf-8"))
        return self.add_file(file=buffer, file_name=name, metadata=metadata)

    def get_files(self) -> "List[CollectionFile]":
        """Returns the collection's files, refreshed from the server.

        Lets you iterate over a collection's files without knowing their names up front (e.g.
        to review every document). Re-fetches current state, so it reflects files added or
        finished processing since this collection object was loaded.

        Returns
        -------
        List[CollectionFile]

        Examples
        --------
        >>> for f in collection.get_files():
        ...     print(f.name, f.processing_status)
        """
        self.files = [
            CollectionFile._from_dataset_file(f)
            for f in self.datasetfile_service.get_files(self.id)
        ]
        return self.files

    def get_file(self, name_or_id: str) -> CollectionFile:
        """Returns a file in the collection by its name or id.

        Parameters
        ----------
        name_or_id : str
            The file's name (e.g. ``"intro.txt"``) or its id.

        Returns
        -------
        CollectionFile

        Raises
        ------
        ValueError
            Raised if no file in the collection matches the given name or id.
        """
        for f in self.files:
            if f.id == name_or_id or f.name == name_or_id:
                return CollectionFile._from_dataset_file(f)
        raise ValueError(f"No file named or with id '{name_or_id}' in this collection.")

    def link(
        self,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
        linking_profile: Optional[dict] = None,
    ) -> None:
        """Runs batch subject-linking reconciliation over the entire collection.

        Linking is decoupled from detection: adding files detects PII, but the subjects are not
        (re)built until you call ``link()``. Reconciliation looks at every file's entities at once,
        groups them into canonical subjects (deterministically, regardless of upload order), and
        replaces the collection's subject graph atomically. Call it after files finish processing —
        and again after adding more files — to rebuild the graph.

        Only one linking run happens per collection at a time; calling again while one is in
        flight attaches to the running job rather than starting a second.

        Parameters
        ----------
        wait : bool
            When True, block until the linking job finishes (or fails / times out) instead of
            returning as soon as it is queued.
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.
        linking_profile : Optional[dict]
            A declarative linking profile describing how subjects are clustered, merged, related,
            and synthesized. When omitted (None), the server uses its built-in default profile, so
            existing callers are unaffected. Invalid profiles are rejected by the server with a 400.

        Raises
        ------
        RuntimeError
            Raised when ``wait`` is True and the linking job ends in a non-completed state.
        TimeoutError
            Raised when ``wait`` is True and the job does not finish within ``timeout_seconds``.

        Examples
        --------
        >>> collection.link(wait=True)
        >>> graph = collection.get_subject_graph()
        """
        body = {"linkingProfile": linking_profile} if linking_profile is not None else {}
        job = self.client.http_post(f"/api/dataset/{self.id}/link", data=body)
        if not wait:
            return

        job_id = job.get("id") if isinstance(job, dict) else None
        terminal = {"Completed", "Failed", "Canceled", "Skipped"}
        deadline = time.monotonic() + timeout_seconds
        while True:
            status = self.get_subject_linking_status()
            state = status.get("status") if status else None
            # Match the job we started so a stale prior run's "Completed" can't end the wait early.
            current = status and (job_id is None or status.get("id") == job_id)
            if current and state in terminal:
                if state != "Completed":
                    raise RuntimeError(
                        f"Subject linking for collection '{self.name}' ended with status '{state}'."
                    )
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Subject linking for collection '{self.name}' did not finish within "
                    f"{timeout_seconds} seconds."
                )
            time.sleep(poll_interval_seconds)

    def get_subject_linking_status(self) -> Optional[dict]:
        """Returns the latest subject-linking job for the collection, or ``None`` if never linked.

        The returned dict mirrors the job model (``status``, ``startTime``, ``endTime``, ...).
        "Done" means a ``status`` of ``"Completed"`` with no run currently in flight.

        Returns
        -------
        Optional[dict]
        """
        with requests.Session() as session:
            return self.client.http_get(
                f"/api/dataset/{self.id}/subject-linking-status",
                session=session,
            )

    def synthesize(
        self,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
    ) -> None:
        """Runs phase 2 of linking: synthesizes the reconciled subject graph.

        ``link()`` only reconciles — it groups mentions into subjects and persists the graph WITHOUT
        synthetic values, so the graph can be inspected and enriched (``add_relationship`` /
        ``create_subject`` / ``merge_subjects``) first. ``synthesize()`` then generates the coherent
        synthetic bundles over that graph (honoring any enrichments) and atomically re-persists it.
        Requires a reconciled graph to exist (call ``link()`` first); reuses the profile ``link()`` ran
        with. Only one synthesis run happens per collection at a time.

        Parameters
        ----------
        wait : bool
            When True, block until the synthesis job finishes (or fails / times out).
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.

        Raises
        ------
        RuntimeError
            Raised when ``wait`` is True and the synthesis job ends in a non-completed state.
        TimeoutError
            Raised when ``wait`` is True and the job does not finish within ``timeout_seconds``.

        Examples
        --------
        >>> collection.link(wait=True)
        >>> # ... optionally enrich the graph here ...
        >>> collection.synthesize(wait=True)
        >>> graph = collection.get_subject_graph()
        """
        job = self.client.http_post(f"/api/dataset/{self.id}/synthesize")
        if not wait:
            return

        job_id = job.get("id") if isinstance(job, dict) else None
        terminal = {"Completed", "Failed", "Canceled", "Skipped"}
        deadline = time.monotonic() + timeout_seconds
        while True:
            status = self.get_subject_synthesis_status()
            state = status.get("status") if status else None
            current = status and (job_id is None or status.get("id") == job_id)
            if current and state in terminal:
                if state != "Completed":
                    raise RuntimeError(
                        f"Subject synthesis for collection '{self.name}' ended with status '{state}'."
                    )
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Subject synthesis for collection '{self.name}' did not finish within "
                    f"{timeout_seconds} seconds."
                )
            time.sleep(poll_interval_seconds)

    def get_subject_synthesis_status(self) -> Optional[dict]:
        """Returns the latest subject-synthesis job for the collection, or ``None`` if never run.

        The returned dict mirrors the job model (``status``, ``startTime``, ``endTime``, ...).

        Returns
        -------
        Optional[dict]
        """
        with requests.Session() as session:
            return self.client.http_get(
                f"/api/dataset/{self.id}/subject-synthesis-status",
                session=session,
            )

    def create_subject(
        self,
        identity_type: str,
        named_entity_ids: Optional[List[str]] = None,
    ) -> dict:
        """Creates a new subject in the reconciled graph (enrichment step, before ``synthesize``).

        Parameters
        ----------
        identity_type : str
            The subject's identity type (e.g. ``"Person"``, ``"Organization"``, ``"SlackUsername"``).
        named_entity_ids : Optional[List[str]]
            Ids of existing detected entities in the collection to group under the new subject.

        Returns
        -------
        dict
            ``{"id": ..., "identityType": ...}`` for the created subject.
        """
        body = {"identityType": identity_type, "namedEntityIds": named_entity_ids or []}
        return self.client.http_post(f"/api/dataset/{self.id}/subjects", data=body)

    def add_relationship(
        self,
        left_subject_id: str,
        right_subject_id: str,
        relationship_type: str,
        confidence: Optional[float] = None,
    ) -> dict:
        """Adds a directed relationship edge between two subjects (enrichment step, before ``synthesize``).

        Parameters
        ----------
        left_subject_id, right_subject_id : str
            The edge endpoints (both must be subjects of this collection).
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
        return self.client.http_post(f"/api/dataset/{self.id}/relationships", data=body)

    def merge_subjects(self, survivor_subject_id: str, loser_subject_id: str) -> None:
        """Merges ``loser_subject_id`` into ``survivor_subject_id`` (enrichment step, before ``synthesize``).

        The loser's links and relationships move to the survivor (self-loops and duplicates dropped),
        then the loser subject is deleted.
        """
        body = {
            "survivorSubjectId": survivor_subject_id,
            "loserSubjectId": loser_subject_id,
        }
        self.client.http_post(f"/api/dataset/{self.id}/subjects/merge", data=body)

    def delete_relationship(self, relationship_id: str) -> None:
        """Deletes a single relationship edge (enrichment step, before ``synthesize``).

        Use to remove a wrong edge — e.g. an LLM-inferred ownership edge that ``users.json`` refutes.
        Pair with ``add_relationship`` to repoint an edge to the correct subject.
        """
        self.client.http_delete(f"/api/dataset/{self.id}/relationships/{relationship_id}")

    def get_subject_graph(self) -> CollectionSubjectGraph:
        """Returns every subject across the whole collection and how they relate.

        This is the collection-wide companion to ``CollectionFile.get_subject_graph()``:
        subjects here may span multiple files (cross-document linking merges mentions of the
        same identity), and the result carries summary statistics about the collection.

        Call this only after files have finished processing **and** after ``link()`` has completed
        (use ``link(wait=True)`` or poll ``get_subject_linking_status()``) — otherwise the graph
        reflects a stale or empty linking run.

        Returns
        -------
        CollectionSubjectGraph
            All subjects, their relationships, and collection-level stats.

        Examples
        --------
        >>> collection.link(wait=True)
        >>> graph = collection.get_subject_graph()
        >>> print(graph.describe())
        """
        with requests.Session() as session:
            response = self.client.http_get(
                f"/api/dataset/{self.id}/subjects-graph",
                session=session,
            )
        return CollectionSubjectGraph.from_dict(response, collection_name=self.name)

    def render_document(
        self,
        document_id: str,
        text: Optional[str] = None,
        random_seed: Optional[int] = None,
    ) -> str:
        """Renders one document's synthetic text from the FROZEN subject graph (synthesize phase).

        Splices the persisted graph's synthetic values into the document at its stored entity
        offsets. Byte-identical to downloading the document, with one addition: you may re-supply
        the document's original text via ``text`` ("discard mode") so the server splices without
        reading stored content. The re-supplied text must be byte-identical to what was ingested,
        or the offset splices misalign.

        Run ``synthesize()`` first so the graph carries synthetic values. This reads from the
        persisted graph (unlike stateless ``redact`` calls, which recompute in memory), so its
        output matches the collection's other documents for cross-document consistency.

        Parameters
        ----------
        document_id : str
            The document id — a collection file id (e.g. from ``add_text`` or ``get_files``).
        text : Optional[str]
            Byte-identical original text to splice into. When omitted, the stored original is used.
        random_seed : Optional[int]
            Optional seed override (same semantics as ``CollectionFile.download``) so entities not
            covered by the graph render deterministically. Use the same seed you download with to
            get identical output.

        Returns
        -------
        str
            The document's synthetic text.

        Examples
        --------
        >>> doc = collection.add_text("Meg, did Sheryl at Hoosier Endo email you?")
        >>> collection.link(wait=True); collection.synthesize(wait=True)
        >>> collection.render_document(doc.id)                       # stored mode
        >>> collection.render_document(doc.id, text=original_text)   # discard mode
        """
        body = {} if text is None else {"text": text}
        headers = (
            {"textual-random-seed": str(random_seed)} if random_seed is not None else {}
        )
        response = self.client.http_post(
            f"/api/dataset/{self.id}/documents/{document_id}/render",
            data=body,
            additional_headers=headers,
        )
        if isinstance(response, dict):
            return response.get("synthetic", "")
        return response

    def iter_reviews(self) -> Iterator[FileReview]:
        """Yields an original-vs-synthetic review for each file in the collection.

        Iterate this to walk the collection document by document, comparing what synthesis
        changed in each one.

        Yields
        ------
        FileReview

        Examples
        --------
        >>> for review in collection.iter_reviews():
        ...     print(review.describe())
        """
        for f in self.files:
            yield CollectionFile._from_dataset_file(f).get_review()

    def replacement_pairs(self) -> "List[tuple[str, str, str, int]]":
        """Returns every distinct (entity type, original, synthetic) replacement across the collection.

        Aggregates the changed spans from every file's review and deduplicates them, so a value
        that always maps the same way appears once. Each entry is
        ``(entity_type, original, synthetic, count)`` where ``count`` is how many times that exact
        triple occurred across all files. A value that maps inconsistently surfaces as multiple
        entries sharing the same original — e.g. ``("ORGANIZATION", "Lilly", "Vector", 58)`` and
        ``("ORGANIZATION", "Lilly", "Acme", 2)`` — which is how you spot drift.

        Sorted by entity type, then original (case-insensitive), then by descending count, so each
        type's rows are grouped together and within a type the dominant mapping for each original
        comes first with rare/odd ones just beneath it.

        Returns
        -------
        List[tuple[str, str, str, int]]
            Distinct ``(entity_type, original, synthetic, count)`` quadruples.
        """
        from collections import Counter

        counts: "Counter[tuple[str, str, str]]" = Counter()
        for review in self.iter_reviews():
            for change in review.to_dict()["changes"]:
                entity_type = (change.get("entity_type") or "").strip() or "UNKNOWN"
                original = (change["original"] or "").strip() or "∅"
                synthetic = (change["synthetic"] or "").strip() or "∅"
                counts[(entity_type, original, synthetic)] += 1

        return [
            (entity_type, original, synthetic, count)
            for (entity_type, original, synthetic), count in sorted(
                counts.items(),
                key=lambda kv: (
                    kv[0][0].casefold(),
                    kv[0][1].casefold(),
                    -kv[1],
                    kv[0][2].casefold(),
                ),
            )
        ]

    def describe_replacements(self, max_width: int = 60) -> str:
        """Returns a deduplicated two-column table of original → synthetic replacements.

        The scannable, collection-wide companion to the per-file ``iter_reviews()`` diff — built
        for reviewing many files at once. One row per distinct ``(original, synthetic)`` pair
        (with an occurrence count), so consistent replacements collapse to a single line and any
        original that maps to more than one synthetic shows a row per target, grouped together and
        flagged, so inconsistencies jump out.

        Parameters
        ----------
        max_width : int
            Column values longer than this are truncated with an ellipsis.

        Examples
        --------
        >>> print(collection.describe_replacements())
        """
        rows = self.replacement_pairs()
        if not rows:
            return "No replacements found across the collection."

        # Originals that map to more than one distinct synthetic — the drift to look at.
        synthetics_per_original: dict = {}
        for _entity_type, original, synthetic, _count in rows:
            synthetics_per_original.setdefault(original, set()).add(synthetic)
        inconsistent = {o for o, s in synthetics_per_original.items() if len(s) > 1}

        def clip(value: str) -> str:
            return value if len(value) <= max_width else value[: max_width - 1] + "…"

        type_header, orig_header, synth_header = "ENTITY TYPE", "ORIGINAL", "SYNTHETIC"
        type_w = max(len(type_header), max(len(clip(t)) for t, _, _, _ in rows))
        orig_w = max(len(orig_header), max(len(clip(o)) for _, o, _, _ in rows))
        synth_w = max(len(synth_header), max(len(clip(s)) for _, _, s, _ in rows))

        lines = [
            f"{len(rows)} distinct replacement pair(s)"
            + (f"; {len(inconsistent)} original(s) map to >1 synthetic" if inconsistent else ""),
            f"{type_header.ljust(type_w)}  {orig_header.ljust(orig_w)}  {synth_header.ljust(synth_w)}  COUNT",
            f"{'-' * type_w}  {'-' * orig_w}  {'-' * synth_w}  -----",
        ]
        for entity_type, original, synthetic, count in rows:
            flag = " *" if original in inconsistent else ""
            lines.append(
                f"{clip(entity_type).ljust(type_w)}  {clip(original).ljust(orig_w)}  "
                f"{clip(synthetic).ljust(synth_w)}  {count:>5}{flag}"
            )
        if inconsistent:
            lines.append("")
            lines.append("* original maps to more than one synthetic value (possible inconsistency)")
        return "\n".join(lines)

    def synthesize_linked_entities_only(
        self, should_rescan: bool = True, preserve_name_gender: bool = True
    ) -> None:
        """Configures the collection to synthesize only the subject-linking entity types.

        Sets every entity type's default to Off and turns the subject-linking labels (the ones
        in :data:`SUBJECT_LINKING_ENTITY_LABELS`) to Synthesis, so the only transformed values
        are the ones that participate in subjects. (The default is applied by setting every
        type to Off explicitly — the backend fills any omitted type with Redaction, not Off.)

        Parameters
        ----------
        should_rescan : bool
            When True (default), re-scans existing files so they re-synthesize under the new
            configuration. Pass False when configuring a collection that has no files yet.
        preserve_name_gender : bool
            When True (default), synthesized given names keep the original name's gender (male
            names map to male names, etc.) when it can be determined.
        """
        generator_config = {name: PiiState.Off for name in PiiType._member_names_}
        for label in SUBJECT_LINKING_ENTITY_LABELS:
            generator_config[label] = PiiState.Synthesis

        generator_metadata = None
        if preserve_name_gender:
            # Applies to the name labels that produce gendered given names.
            generator_metadata = {
                "NAME_GIVEN": NameGeneratorMetadata(preserve_gender=True),
                "PERSON": NameGeneratorMetadata(preserve_gender=True),
            }

        self.edit(
            generator_config=generator_config,
            generator_metadata=generator_metadata,
            should_rescan=should_rescan,
        )
