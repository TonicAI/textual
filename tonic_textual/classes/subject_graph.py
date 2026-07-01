from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

_RESET = "\033[0m"

# ANSI color per identity type, so subjects are easy to tell apart at a glance.
_IDENTITY_COLORS = {
    "Person": "32",        # green
    "Organization": "34",  # blue
    "Email": "36",         # cyan
    "Phone": "33",         # yellow
    "Url": "35",           # magenta
    "Address": "33",       # yellow
}
_DEFAULT_IDENTITY_COLOR = "37"  # white/grey
_RELATIONSHIP_COLOR = "35"      # magenta — distinct from any subject color

# Friendly aliases so callers can group by "company"/"org"/"people" etc.
_IDENTITY_ALIASES = {
    "person": "Person",
    "people": "Person",
    "company": "Organization",
    "companies": "Organization",
    "org": "Organization",
    "organisation": "Organization",
    "organization": "Organization",
    "organizations": "Organization",
    "email": "Email",
    "emails": "Email",
    "phone": "Phone",
    "phones": "Phone",
    "url": "Url",
    "urls": "Url",
    "address": "Address",
    "addresses": "Address",
}
_IDENTITY_PLURALS = {
    "Person": "People",
    "Organization": "Organizations",
    "Email": "Emails",
    "Phone": "Phones",
    "Url": "URLs",
    "Address": "Addresses",
}


def _style(text: str, *codes: str, enabled: bool = True) -> str:
    """Wraps text in ANSI codes when enabled, otherwise returns it unchanged."""
    if not enabled or not codes:
        return text
    return "\033[" + ";".join(codes) + "m" + text + _RESET


def _identity_color(identity_type: str) -> str:
    return _IDENTITY_COLORS.get(identity_type, _DEFAULT_IDENTITY_COLOR)


def _render_subjects(
    subjects: "List[Subject]", use_color: bool, dedupe: bool = False
) -> "List[str]":
    """Renders the 'Subjects (N):' section. Shared by the file and collection views.

    When ``dedupe`` is set, repeated ``(label, text)`` mentions are collapsed to one (useful
    for the collection view, where the same value recurs across files); the per-file view
    keeps every mention.
    """
    lines = [_style(f"Subjects ({len(subjects)}):", "1", enabled=use_color)]
    if not subjects:
        lines.append(
            _style("  (none — files may still be processing)", "2", enabled=use_color)
        )
        return lines

    type_width = max(len(s.identity_type) for s in subjects)
    name_width = max(len(s.display_name) for s in subjects)
    for s in subjects:
        code = _identity_color(s.identity_type)
        # Pad on the plain text, then colorize, so ANSI escapes don't break alignment.
        type_plain = f"[{s.identity_type}]"
        type_col = _style(type_plain, code, enabled=use_color) + " " * (
            type_width + 2 - len(type_plain)
        )
        name_col = _style(s.display_name, code, "1", enabled=use_color) + " " * (
            name_width - len(s.display_name)
        )

        mentions = s.entities
        if dedupe:
            seen: set = set()
            mentions = []
            for e in s.entities:
                key = (e.label, e.text)
                if key in seen:
                    continue
                seen.add(key)
                mentions.append(e)

        # Skip the entity detail when it would just repeat the display name (e.g. a
        # single-mention Email or Organization subject).
        redundant = len(mentions) == 1 and mentions[0].text == s.display_name
        extras = (
            ""
            if redundant
            else ", ".join(f'{e.label} "{e.text}"' for e in mentions)
        )
        line = f"  {type_col}  {name_col}"
        if extras:
            line += "  " + _style(f"— {extras}", "2", enabled=use_color)
        lines.append(line.rstrip())
    return lines


def _render_relationships(
    relationships: "List[Relationship]",
    by_id: "Dict[str, Subject]",
    use_color: bool,
) -> "List[str]":
    """Renders the 'Relationships (N):' section. Shared by the file and collection views."""
    lines = [
        _style(f"Relationships ({len(relationships)}):", "1", enabled=use_color)
    ]
    if not relationships:
        lines.append(_style("  (none)", "2", enabled=use_color))
        return lines

    for r in relationships:
        left = by_id.get(r.left_subject_id)
        right = by_id.get(r.right_subject_id)
        left_name = left.display_name if left else r.left_subject_id
        right_name = right.display_name if right else r.right_subject_id
        left_col = _style(
            left_name,
            _identity_color(left.identity_type) if left else _DEFAULT_IDENTITY_COLOR,
            enabled=use_color,
        )
        right_col = _style(
            right_name,
            _identity_color(right.identity_type) if right else _DEFAULT_IDENTITY_COLOR,
            enabled=use_color,
        )
        rel = _style(f"──{r.type}──▶", _RELATIONSHIP_COLOR, "1", enabled=use_color)
        method = (r.derivation_method or "").lower()
        meta = _style(f"({method}, {r.confidence:.2f})", "2", enabled=use_color)
        lines.append(f"  {left_col} {rel} {right_col}  {meta}")
    return lines


class SubjectEntity:
    """A single detected PII mention that is linked to a subject.

    These are the raw entities (a name, an email, a phone number) that the linker groups
    together under one subject.
    """

    def __init__(
        self,
        entity_id: str,
        label: str,
        text: str,
        confidence: float,
        link_method: str,
        file_id: str,
        file_name: str,
        row_number: int,
        start: int,
        end: int,
        job_id: str,
    ):
        self.entity_id = entity_id
        self.label = label
        self.text = text
        self.confidence = confidence
        self.link_method = link_method
        self.file_id = file_id
        self.file_name = file_name
        self.row_number = row_number
        self.start = start
        self.end = end
        self.job_id = job_id

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SubjectEntity":
        return cls(
            entity_id=d["entityId"],
            label=d.get("label", ""),
            text=d.get("text", ""),
            confidence=d.get("confidence", 0.0),
            link_method=d.get("linkMethod", ""),
            file_id=d.get("fileId", ""),
            file_name=d.get("fileName", ""),
            row_number=d.get("rowNumber", 0),
            start=d.get("start", 0),
            end=d.get("end", 0),
            job_id=d.get("jobId", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "label": self.label,
            "text": self.text,
            "confidence": self.confidence,
            "link_method": self.link_method,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "row_number": self.row_number,
            "start": self.start,
            "end": self.end,
            "job_id": self.job_id,
        }


class Subject:
    """A linked identity within a file: a person, organization, or one of their identifiers.

    A subject groups the entities that refer to the same thing (e.g. a person's given name,
    family name, and email all link to one Person subject).
    """

    def __init__(
        self,
        id: str,
        identity_type: str,
        entity_count: int,
        entities: List[SubjectEntity],
        synthetic_name: Optional[str] = None,
        synthetic_email: Optional[str] = None,
        synthetic_phone: Optional[str] = None,
    ):
        self.id = id
        self.identity_type = identity_type
        self.entity_count = entity_count
        self.entities = entities
        # The synthetic identity Textual will substitute in (from the subject's bundle).
        self.synthetic_name = synthetic_name
        self.synthetic_email = synthetic_email
        self.synthetic_phone = synthetic_phone

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Subject":
        bundle = d.get("bundle") or {}
        entities = [SubjectEntity.from_dict(e) for e in d.get("entities", [])]
        return cls(
            id=d["id"],
            identity_type=d.get("identityType", ""),
            entity_count=d.get("entityCount", len(entities)),
            entities=entities,
            synthetic_name=bundle.get("primaryName"),
            synthetic_email=bundle.get("primaryEmail"),
            synthetic_phone=bundle.get("primaryPhone"),
        )

    def _first_text(self, *labels: str) -> Optional[str]:
        for label in labels:
            for e in self.entities:
                if e.label == label:
                    return e.text
        return None

    @property
    def display_name(self) -> str:
        """A human-readable label for the subject, built from its originally detected text.

        Uses the original entity text (not the synthetic value) so the graph reflects what
        was actually found in the file.
        """
        if self.identity_type == "Person":
            given = self._first_text("NAME_GIVEN")
            family = self._first_text("NAME_FAMILY")
            name = " ".join(p for p in (given, family) if p)
            if name:
                return name
            person = self._first_text("PERSON")
            if person:
                return person
        elif self.identity_type == "Organization":
            org = self._first_text("ORGANIZATION")
            if org:
                return org

        # Email / Phone / Url / Address (and any unknown type): the single mention is the
        # identity itself.
        if self.entities:
            return self.entities[0].text
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity_type": self.identity_type,
            "display_name": self.display_name,
            "entity_count": self.entity_count,
            "synthetic_name": self.synthetic_name,
            "synthetic_email": self.synthetic_email,
            "synthetic_phone": self.synthetic_phone,
            "entities": [e.to_dict() for e in self.entities],
        }


class Relationship:
    """A directed edge between two subjects (e.g. a person ``WorksAt`` an organization)."""

    def __init__(
        self,
        id: str,
        left_subject_id: str,
        right_subject_id: str,
        type: str,
        confidence: float,
        derivation_method: str,
        derived_by_rule: Optional[str] = None,
    ):
        self.id = id
        self.left_subject_id = left_subject_id
        self.right_subject_id = right_subject_id
        self.type = type
        self.confidence = confidence
        # How the edge was derived: "Rule", "Llm", or "Manual".
        self.derivation_method = derivation_method
        self.derived_by_rule = derived_by_rule

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Relationship":
        return cls(
            id=d.get("id", ""),
            left_subject_id=d["leftSubjectId"],
            right_subject_id=d["rightSubjectId"],
            type=d.get("type", ""),
            confidence=d.get("confidence", 0.0),
            derivation_method=d.get("derivationMethod", ""),
            derived_by_rule=d.get("derivedByRule"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "left_subject_id": self.left_subject_id,
            "right_subject_id": self.right_subject_id,
            "confidence": self.confidence,
            "derivation_method": self.derivation_method,
            "derived_by_rule": self.derived_by_rule,
        }


class FileSubjectGraph:
    """The subjects found in a single file and the relationships among them."""

    def __init__(
        self,
        subjects: List[Subject],
        relationships: List[Relationship],
        file_name: Optional[str] = None,
    ):
        self.subjects = subjects
        self.relationships = relationships
        self.file_name = file_name
        self._by_id = {s.id: s for s in subjects}

    @classmethod
    def from_dict(
        cls, d: Dict[str, Any], file_name: Optional[str] = None
    ) -> "FileSubjectGraph":
        subjects = [Subject.from_dict(s) for s in d.get("subjects", [])]
        relationships = [Relationship.from_dict(r) for r in d.get("relationships", [])]
        return cls(subjects, relationships, file_name)

    def subject(self, subject_id: str) -> Optional[Subject]:
        """Returns the subject with the given id, or None if it isn't in this graph."""
        return self._by_id.get(subject_id)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable view of the graph."""
        return {
            "file_name": self.file_name,
            "subjects": [s.to_dict() for s in self.subjects],
            "relationships": [r.to_dict() for r in self.relationships],
        }

    def describe(self, color: Optional[bool] = None) -> str:
        """Returns a human-readable rendering of the subjects and their relationships.

        Parameters
        ----------
        color : Optional[bool]
            Whether to colorize the output with ANSI codes. Defaults to auto-detection:
            on when stdout is a terminal, off otherwise (so piped/redirected output stays
            plain). Pass ``True`` or ``False`` to force it.
        """
        use_color = sys.stdout.isatty() if color is None else color
        lines: List[str] = []

        if self.file_name:
            label = _style("File:", "2", enabled=use_color)
            name = _style(self.file_name, "1", enabled=use_color)  # bold
            lines.append(f"{label} {name}")

        lines += _render_subjects(self.subjects, use_color)
        lines += _render_relationships(self.relationships, self._by_id, use_color)
        return "\n".join(lines)


class CollectionStats:
    """Summary counts for a collection's subject graph, shown at the top of the view."""

    def __init__(
        self,
        file_count: int,
        subject_count: int,
        subjects_by_type: Dict[str, int],
        relationship_count: int,
        relationships_by_type: Dict[str, int],
        entity_count: int,
        cross_file_subject_count: int,
    ):
        self.file_count = file_count
        self.subject_count = subject_count
        self.subjects_by_type = subjects_by_type
        self.relationship_count = relationship_count
        self.relationships_by_type = relationships_by_type
        self.entity_count = entity_count
        # Subjects whose linked entities span two or more files — the headline signal that
        # cross-document linking is actually connecting identities.
        self.cross_file_subject_count = cross_file_subject_count

    @classmethod
    def from_graph(
        cls, subjects: "List[Subject]", relationships: "List[Relationship]"
    ) -> "CollectionStats":
        files: set = set()
        subjects_by_type: Dict[str, int] = {}
        entity_count = 0
        cross_file = 0
        for s in subjects:
            subjects_by_type[s.identity_type] = subjects_by_type.get(s.identity_type, 0) + 1
            entity_count += len(s.entities)
            file_ids = {e.file_id for e in s.entities if e.file_id}
            files.update(file_ids)
            if len(file_ids) >= 2:
                cross_file += 1

        relationships_by_type: Dict[str, int] = {}
        for r in relationships:
            relationships_by_type[r.type] = relationships_by_type.get(r.type, 0) + 1

        return cls(
            file_count=len(files),
            subject_count=len(subjects),
            subjects_by_type=subjects_by_type,
            relationship_count=len(relationships),
            relationships_by_type=relationships_by_type,
            entity_count=entity_count,
            cross_file_subject_count=cross_file,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_count": self.file_count,
            "subject_count": self.subject_count,
            "subjects_by_type": self.subjects_by_type,
            "relationship_count": self.relationship_count,
            "relationships_by_type": self.relationships_by_type,
            "entity_count": self.entity_count,
            "cross_file_subject_count": self.cross_file_subject_count,
        }


class CollectionSubjectGraph:
    """Every subject in a collection and the relationships among them, with summary stats.

    The whole-collection analogue of :class:`FileSubjectGraph`. Subjects here may span
    multiple files (cross-document linking merges them into one canonical subject).
    """

    def __init__(
        self,
        subjects: List[Subject],
        relationships: List[Relationship],
        collection_name: Optional[str] = None,
    ):
        self.subjects = subjects
        self.relationships = relationships
        self.collection_name = collection_name
        self._by_id = {s.id: s for s in subjects}
        self.stats = CollectionStats.from_graph(subjects, relationships)

    @classmethod
    def from_dict(
        cls, d: Dict[str, Any], collection_name: Optional[str] = None
    ) -> "CollectionSubjectGraph":
        subjects = [Subject.from_dict(s) for s in d.get("subjects", [])]
        relationships = [Relationship.from_dict(r) for r in d.get("relationships", [])]
        return cls(subjects, relationships, collection_name)

    def subject(self, subject_id: str) -> Optional[Subject]:
        """Returns the subject with the given id, or None if it isn't in this graph."""
        return self._by_id.get(subject_id)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable view of the collection graph."""
        return {
            "collection_name": self.collection_name,
            "stats": self.stats.to_dict(),
            "subjects": [s.to_dict() for s in self.subjects],
            "relationships": [r.to_dict() for r in self.relationships],
        }

    def _stats_header(self, use_color: bool) -> List[str]:
        st = self.stats
        lines: List[str] = []
        if self.collection_name:
            label = _style("Collection:", "2", enabled=use_color)
            name = _style(self.collection_name, "1", enabled=use_color)
            lines.append(f"{label} {name}")

        def num(n: int) -> str:
            return _style(str(n), "1", enabled=use_color)

        lines.append(
            f"  Files: {num(st.file_count)}   "
            f"Subjects: {num(st.subject_count)}   "
            f"Relationships: {num(st.relationship_count)}   "
            f"Linked entities: {num(st.entity_count)}"
        )
        if st.subjects_by_type:
            by_type = ", ".join(
                f"{_style(t, _identity_color(t), enabled=use_color)} {c}"
                for t, c in sorted(st.subjects_by_type.items())
            )
            lines.append(f"  By type: {by_type}")
        lines.append(
            "  Cross-file subjects: "
            + _style(str(st.cross_file_subject_count), "1", enabled=use_color)
        )
        return lines

    def describe(self, color: Optional[bool] = None) -> str:
        """Returns a human-readable rendering: stats header, then subjects and relationships.

        Parameters
        ----------
        color : Optional[bool]
            Whether to colorize with ANSI codes. Defaults to auto (on for a terminal).
        """
        use_color = sys.stdout.isatty() if color is None else color
        lines = self._stats_header(use_color)
        lines.append("")
        lines += _render_subjects(self.subjects, use_color, dedupe=True)
        lines += _render_relationships(self.relationships, self._by_id, use_color)
        return "\n".join(lines)

    @staticmethod
    def _normalize_identity(group_by: str) -> str:
        return _IDENTITY_ALIASES.get(group_by.strip().lower(), group_by.strip())

    def _relationships_for(self, subject_id: str) -> "List[tuple]":
        """Returns (relationship_type, other_subject) for every edge touching the subject."""
        out = []
        for r in self.relationships:
            if r.left_subject_id == subject_id:
                out.append((r.type, self._by_id.get(r.right_subject_id)))
            elif r.right_subject_id == subject_id:
                out.append((r.type, self._by_id.get(r.left_subject_id)))
        return out

    def describe_grouped(
        self, group_by: str = "Person", color: Optional[bool] = None
    ) -> str:
        """Enumerates each subject of one identity type and the data associated with it.

        Unlike :meth:`describe` (which draws the whole graph), this groups by identity type
        and, for each member, gathers a full profile: its own detected attributes plus the
        identifiers and organizations linked to it via relationships (e.g. a person's emails,
        phones, and employer — which are themselves separate subjects).

        Parameters
        ----------
        group_by : str
            The identity type to enumerate. Accepts friendly aliases, e.g. ``"person"``,
            ``"people"``, ``"company"``/``"org"`` (Organization), ``"email"``, ``"phone"``.
        color : Optional[bool]
            Whether to colorize with ANSI codes. Defaults to auto (on for a terminal).
        """
        use_color = sys.stdout.isatty() if color is None else color
        target = self._normalize_identity(group_by)
        members = [s for s in self.subjects if s.identity_type == target]
        plural = _IDENTITY_PLURALS.get(target, target + "s")

        lines = [_style(f"{plural} ({len(members)}):", "1", enabled=use_color)]
        if not members:
            lines.append(_style("  (none)", "2", enabled=use_color))
            return "\n".join(lines)

        code = _identity_color(target)
        for s in members:
            lines.append("")
            lines.append("  " + _style(s.display_name, code, "1", enabled=use_color))

            # The subject's own detected attributes, grouped by label and de-duplicated.
            by_label: Dict[str, List[str]] = {}
            for e in s.entities:
                vals = by_label.setdefault(e.label, [])
                if e.text not in vals:
                    vals.append(e.text)
            for label, vals in by_label.items():
                lbl = _style(f"{label}:", "2", enabled=use_color)
                lines.append(f"    {lbl} {', '.join(vals)}")

            # Linked identifiers / organizations, grouped by relationship type.
            rels: Dict[str, List[Subject]] = {}
            seen_edges: set = set()
            for rtype, other in self._relationships_for(s.id):
                other_id = other.id if other else None
                if (rtype, other_id) in seen_edges:
                    continue
                seen_edges.add((rtype, other_id))
                rels.setdefault(rtype, []).append(other)
            for rtype, others in rels.items():
                names = ", ".join(
                    _style(
                        o.display_name,
                        _identity_color(o.identity_type),
                        enabled=use_color,
                    )
                    if o
                    else "?"
                    for o in others
                )
                arrow = _style(f"{rtype} →", _RELATIONSHIP_COLOR, "1", enabled=use_color)
                lines.append(f"    {arrow} {names}")

            # Synthetic identity preview, when present.
            synth = ", ".join(
                v
                for v in (s.synthetic_name, s.synthetic_email, s.synthetic_phone)
                if v
            )
            if synth:
                lines.append(
                    "    " + _style(f"synthetic: {synth}", "2", enabled=use_color)
                )

            # Files this subject appears in.
            files: List[str] = []
            for e in s.entities:
                fn = e.file_name or e.file_id
                if fn and fn not in files:
                    files.append(fn)
            if files:
                lines.append(
                    "    " + _style(f"files: {', '.join(files)}", "2", enabled=use_color)
                )

        return "\n".join(lines)
