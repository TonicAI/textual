from __future__ import annotations

import difflib
import re
import sys
from typing import Any, Dict, List, Optional

_RESET = "\033[0m"


# Punctuation that the diff may glue onto a changed span (e.g. "Smith." / "Doe,") but that the
# detected entity's value usually omits. Stripped as a fallback when an as-is lookup misses.
_EDGE_PUNCT = ".,;:!?\"'`()[]{}…"


def _resolve_label(original: str, entity_labels: Dict[str, str]) -> str:
    """Best-effort entity type for a changed span, looked up from the file's detected entities.

    The diff works on text and has no label of its own, so we map the changed original value back
    to the label of the entity that produced it. Exact match first; for a coalesced multi-entity
    span (e.g. ``"John Smith"`` from a NAME_GIVEN + NAME_FAMILY pair) we resolve each token and
    combine — collapsing to a shared prefix (``NAME``) when the parts agree, else joining them.
    Each lookup is tried as-is and then with edge punctuation stripped, since the diff can glue a
    trailing ``.``/``,`` onto a span. Returns ``"UNKNOWN"`` when nothing matches.
    """
    if not entity_labels:
        return "UNKNOWN"

    def lookup(value: str) -> "Optional[str]":
        return entity_labels.get(value) or entity_labels.get(value.strip(_EDGE_PUNCT))

    key = original.strip()
    exact = lookup(key)
    if exact:
        return exact

    found: List[str] = []
    for token in key.split():
        label = lookup(token)
        if label and label not in found:
            found.append(label)

    if not found:
        return "UNKNOWN"
    if len(found) == 1:
        return found[0]
    prefixes = {label.split("_", 1)[0] for label in found}
    if len(prefixes) == 1:
        return next(iter(prefixes))
    return "/".join(sorted(found))


def _style(text: str, *codes: str, enabled: bool = True) -> str:
    """Wraps text in ANSI codes when enabled, otherwise returns it unchanged."""
    if not enabled or not codes or text == "":
        return text
    return "\033[" + ";".join(codes) + "m" + text + _RESET


# Split into words and the whitespace between them, keeping both, so equal runs reproduce
# the original spacing exactly when re-joined.
_TOKEN_RE = re.compile(r"\S+|\s+")


class FileReview:
    """A side-by-side-in-place comparison of one document's original vs. synthetic text.

    Renders the document with each changed span shown inline as ``[original → synthetic]`` so
    a reviewer can see exactly what synthesis replaced, in context.
    """

    def __init__(
        self,
        file_name: str,
        original: str,
        synthetic: str,
        entity_labels: Optional[Dict[str, str]] = None,
    ):
        self.file_name = file_name
        self.original = original
        self.synthetic = synthetic
        # Maps an entity's original value to its detected label, so changed spans can be tagged with
        # an entity type (the diff itself is label-free). Empty when labels aren't available.
        self.entity_labels = entity_labels or {}

    def _raw_segments(self) -> "List[tuple]":
        original_tokens = _TOKEN_RE.findall(self.original)
        synthetic_tokens = _TOKEN_RE.findall(self.synthetic)
        matcher = difflib.SequenceMatcher(
            a=original_tokens, b=synthetic_tokens, autojunk=False
        )
        segments = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            kind = "equal" if tag == "equal" else "change"
            segments.append(
                (kind, "".join(original_tokens[i1:i2]), "".join(synthetic_tokens[j1:j2]))
            )
        return segments

    def _segments(self) -> "List[tuple]":
        """Diff segments, coalescing adjacent changes separated only by whitespace.

        So 'John Smith → Ladawn Orlinsky' reads as one change rather than two, while a change
        separated by an unchanged word (e.g. 'joined') stays split.
        """
        raw = self._raw_segments()
        merged: List[tuple] = []
        i = 0
        while i < len(raw):
            kind, original, synthetic = raw[i]
            if kind == "change":
                j = i
                while (
                    j + 2 < len(raw)
                    and raw[j + 1][0] == "equal"
                    and raw[j + 1][1].strip() == ""
                    and raw[j + 2][0] == "change"
                ):
                    whitespace = raw[j + 1][1]
                    original += whitespace + raw[j + 2][1]
                    synthetic += whitespace + raw[j + 2][2]
                    j += 2
                merged.append(("change", original, synthetic))
                i = j + 1
            else:
                merged.append((kind, original, synthetic))
                i += 1
        return merged

    @property
    def change_count(self) -> int:
        """Number of substantive (non-whitespace) changed spans."""
        count = 0
        for kind, original, synthetic in self._segments():
            if kind == "change" and not (
                original.strip() == "" and synthetic.strip() == ""
            ):
                count += 1
        return count

    def _format_change(self, original: str, synthetic: str, use_color: bool) -> str:
        # Whitespace-only change: emit as-is rather than bracketing noise.
        if original.strip() == "" and synthetic.strip() == "":
            return original or synthetic

        original_part = _style(original, "9", "31", enabled=use_color)  # strikethrough red
        synthetic_part = _style(synthetic, "32", enabled=use_color)  # green
        if original and synthetic:
            inner = f"{original_part} → {synthetic_part}"
        elif original:
            inner = f"{original_part} → ∅"
        else:
            inner = f"+{synthetic_part}"

        return (
            _style("[", "2", enabled=use_color)
            + inner
            + _style("]", "2", enabled=use_color)
        )

    def describe(self, color: bool | None = None) -> str:
        """Returns the document rendered with changed spans highlighted inline.

        Parameters
        ----------
        color : Optional[bool]
            Whether to colorize with ANSI codes. Defaults to auto (on for a terminal).
        """
        use_color = sys.stdout.isatty() if color is None else color

        header = (
            _style("File:", "2", enabled=use_color)
            + " "
            + _style(self.file_name, "1", enabled=use_color)
        )
        if not self.original and not self.synthetic:
            return header + "\n  (no content to review)"

        n = self.change_count
        header += "  " + _style(
            f"({n} change{'s' if n != 1 else ''})", "2", enabled=use_color
        )

        parts: List[str] = []
        for kind, original, synthetic in self._segments():
            if kind == "equal":
                parts.append(original)
            else:
                parts.append(self._format_change(original, synthetic, use_color))

        return header + "\n" + "".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable view: the texts plus the list of changed spans.

        Each change carries an ``entity_type`` resolved from the file's detected entities (or
        ``"UNKNOWN"`` when it can't be determined).
        """
        changes = [
            {
                "entity_type": _resolve_label(original, self.entity_labels),
                "original": original,
                "synthetic": synthetic,
            }
            for kind, original, synthetic in self._segments()
            if kind == "change"
            and not (original.strip() == "" and synthetic.strip() == "")
        ]
        return {
            "file_name": self.file_name,
            "original": self.original,
            "synthetic": self.synthetic,
            "changes": changes,
        }
