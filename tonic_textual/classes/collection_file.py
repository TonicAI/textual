from __future__ import annotations

import html as _html
import re as _re
from collections import Counter

import requests

from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.classes.file_review import FileReview
from tonic_textual.classes.subject_graph import FileSubjectGraph


_SPAN_RE = _re.compile(
    r'<span[^>]*\bdata-idx="(\d+)"[^>]*>.*?</span>', _re.IGNORECASE | _re.DOTALL
)

# Block-level closing tags whose boundaries should become line breaks so HTML reads sensibly
# as plain text in a terminal.
_BLOCK_CLOSE_RE = _re.compile(
    r"(?is)</(p|div|li|tr|ul|ol|table|h[1-6]|blockquote|section|article|header|footer)\s*>"
)


def _html_to_readable_text(value: str) -> str:
    """Converts HTML to readable plain text for terminal review.

    Inserts line breaks for ``<br>`` and block-element boundaries, drops all other tags,
    unescapes entities, and collapses runs of blank lines. Content that isn't HTML passes
    through essentially unchanged (just whitespace-normalized), so this is safe to apply to
    plain-text files too.
    """
    if not value:
        return ""
    text = _re.sub(r"(?is)<br\s*/?>", "\n", value)
    text = _BLOCK_CLOSE_RE.sub("\n", text)
    text = _re.sub(r"(?is)<[^>]+>", "", text)
    text = _html.unescape(text)
    text = _re.sub(r"[ \t]+\n", "\n", text)  # trim trailing spaces on each line
    text = _re.sub(r"\n{3,}", "\n\n", text)  # collapse blank-line runs
    return text.strip()


def _flatten_entities(nested) -> list:
    """Flattens the preview's nested [row][column][entity] structure into a flat list whose
    order matches the ``data-idx`` numbering in the HTML."""
    flat = []
    for row in nested or []:
        for column in row or []:
            for entity in column or []:
                flat.append(entity)
    return flat


def _reconstruct_text(preview_html: str, entities: list, value_key: str) -> str:
    """Turns the preview's HTML into plain text, replacing each entity placeholder span with
    the requested value from its entity (e.g. ``text`` for original, ``syntheticText``).

    The preview renders entities as label-only redaction chips
    (``<span data-idx="N">NAME_GIVEN</span>``); the real values live in the entities array,
    indexed by ``data-idx``.
    """
    if not preview_html:
        return ""

    def _replace(match) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(entities):
            return entities[idx].get(value_key) or ""
        return ""

    text = _SPAN_RE.sub(_replace, preview_html)
    return _html_to_readable_text(text)


class CollectionFile(DatasetFile):
    """A file that belongs to a subject collection.

    Carries the file's metadata (name, processing status, row and column counts) and lets you
    download its synthesized output. Returned when you add a file to a collection or list a
    collection's files.
    """

    @classmethod
    def _from_dataset_file(cls, file: DatasetFile) -> "CollectionFile":
        """Re-type a freshly built :class:`DatasetFile` as a :class:`CollectionFile`.

        ``DatasetFile`` instances are constructed fresh per response, so reassigning
        ``__class__`` is safe — it has no shared-instance side effects and preserves every
        populated attribute without mirroring the constructor.
        """
        file.__class__ = cls
        return file  # type: ignore[return-value]

    @property
    def collection_id(self) -> str:
        """The identifier of the subject collection this file belongs to."""
        return self.dataset_id

    def get_subject_graph(self) -> FileSubjectGraph:
        """Returns the subjects detected in this file and the relationships among them.

        Subjects are produced after the file finishes processing, so if linking hasn't run
        yet the graph comes back empty.

        Returns
        -------
        FileSubjectGraph
            The file's subjects and their relationships.

        Examples
        --------
        >>> graph = collection.get_file("intro.txt").get_subject_graph()
        >>> print(graph.describe())
        """
        with requests.Session() as session:
            response = self.client.http_get(
                f"/api/dataset/{self.dataset_id}/files/{self.id}/subjects-graph",
                session=session,
            )
        return FileSubjectGraph.from_dict(response, file_name=self.name)

    def get_review(self) -> FileReview:
        """Returns an original-vs-synthetic comparison of this file's content.

        Pairs the file's parsed original text with its synthesized (redacted) output so the
        changes synthesis made can be reviewed inline. Intended for text-like files.

        Returns
        -------
        FileReview

        Examples
        --------
        >>> print(collection.get_file("intro.txt").get_review().describe())
        """
        # Original text: rebuilt from the preview endpoint, which reconstructs it from the
        # stored source file (no dependency on parse-result retention like /content). The
        # preview renders entities as label-only chips, so we splice the real original values
        # (from originalEntities, indexed by the spans' data-idx) back in.
        with requests.Session() as session:
            preview = self.client.http_get(
                f"/api/preview/{self.dataset_id}/files/{self.id}",
                session=session,
            )
        original_entities = _flatten_entities(preview.get("originalEntities"))
        original = _reconstruct_text(
            preview.get("original") or "", original_entities, "text"
        )

        # Index each entity's original value to its label so the review can tag changed spans with an
        # entity type. A value seen with more than one label resolves to its most frequent (ties broken
        # alphabetically, for determinism).
        label_votes: dict = {}
        for entity in original_entities:
            text = (entity.get("text") or "").strip()
            label = entity.get("label")
            if text and label:
                label_votes.setdefault(text, Counter())[label] += 1
        entity_labels = {
            text: sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            for text, votes in label_votes.items()
        }

        # Synthetic: the authoritative redacted output (subject-linking aware, and it honors
        # the dataset's Off/Synthesis config) — the same bytes a user would download. The
        # preview's own synthetic side is neither, so we don't use it.
        synthetic_bytes = self.download()
        try:
            # Same HTML→readable-text conversion as the original side, so HTML markup that's
            # identical on both sides cancels out and the diff shows only the real changes.
            synthetic = _html_to_readable_text(synthetic_bytes.decode("utf-8"))
        except (UnicodeDecodeError, AttributeError):
            # Non-text / binary synthetic output isn't reviewable as inline text.
            synthetic = ""

        return FileReview(self.name, original, synthetic, entity_labels)
