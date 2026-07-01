from types import SimpleNamespace

from tonic_textual.classes.file_review import FileReview, _resolve_label
from tonic_textual.classes.subject_collection import SubjectCollection


LABELS = {
    "Lilly": "ORGANIZATION",
    "Acme": "ORGANIZATION",
    "John": "NAME_GIVEN",
    "Smith": "NAME_FAMILY",
    "Doe,": "NAME_FAMILY",  # entity text can legitimately carry punctuation
}


class TestResolveLabel:
    def test_exact_match(self):
        assert _resolve_label("Lilly", LABELS) == "ORGANIZATION"

    def test_multi_token_shared_prefix_collapses(self):
        # NAME_GIVEN + NAME_FAMILY -> NAME
        assert _resolve_label("John Smith", LABELS) == "NAME"

    def test_trailing_punctuation_is_stripped_on_lookup(self):
        assert _resolve_label("John Smith.", LABELS) == "NAME"

    def test_entity_text_with_punctuation_matches_as_is(self):
        assert _resolve_label("Doe,", LABELS) == "NAME_FAMILY"

    def test_mixed_unrelated_labels_join_sorted(self):
        assert _resolve_label("John Acme", LABELS) == "NAME_GIVEN/ORGANIZATION"

    def test_no_match_is_unknown(self):
        assert _resolve_label("Nobody", LABELS) == "UNKNOWN"

    def test_no_labels_is_unknown(self):
        assert _resolve_label("anything", {}) == "UNKNOWN"


class TestFileReviewEntityType:
    def test_changes_carry_entity_type(self):
        review = FileReview(
            "f.txt",
            "Hello Lilly and John Smith.",
            "Hello Vector and Ladawn Orlinsky.",
            LABELS,
        )
        by_original = {c["original"]: c["entity_type"] for c in review.to_dict()["changes"]}
        assert by_original["Lilly"] == "ORGANIZATION"
        assert by_original["John Smith."] == "NAME"

    def test_entity_type_unknown_without_labels(self):
        review = FileReview("f.txt", "Hello Lilly", "Hello Vector")
        assert all(c["entity_type"] == "UNKNOWN" for c in review.to_dict()["changes"])


def _review(changes):
    return SimpleNamespace(to_dict=lambda: {"changes": changes})


class _FakeCollection(SubjectCollection):
    def __init__(self, reviews):
        self._reviews = reviews

    def iter_reviews(self):
        return iter(self._reviews)


def _sample_collection():
    return _FakeCollection(
        [
            _review(
                [
                    {"entity_type": "ORGANIZATION", "original": "Lilly", "synthetic": "Vector"},
                    {"entity_type": "NAME", "original": "John Smith", "synthetic": "Ladawn Orlinsky"},
                ]
            ),
            _review(
                [
                    {"entity_type": "ORGANIZATION", "original": "Lilly", "synthetic": "Vector"},
                    {"entity_type": "ORGANIZATION", "original": "Lilly", "synthetic": "Acme"},  # drift
                    {"entity_type": "ORGANIZATION", "original": "Acme Corp", "synthetic": "Zeta"},
                    {"entity_type": "EMAIL_ADDRESS", "original": "a@b.com", "synthetic": "x@y.com"},
                ]
            ),
        ]
    )


class TestReplacementPairs:
    def test_quadruples_with_counts(self):
        pairs = _sample_collection().replacement_pairs()
        assert ("ORGANIZATION", "Lilly", "Vector", 2) in pairs
        assert ("EMAIL_ADDRESS", "a@b.com", "x@y.com", 1) in pairs

    def test_sorted_by_entity_type_then_original(self):
        pairs = _sample_collection().replacement_pairs()
        types = [p[0] for p in pairs]
        assert types == sorted(types, key=str.casefold)
        org = [p for p in pairs if p[0] == "ORGANIZATION"]
        # Alphabetical by original within a type; within an original, dominant mapping first.
        assert org[0][1] == "Acme Corp"
        assert org[1][1:] == ("Lilly", "Vector", 2)
        assert org[2][1:] == ("Lilly", "Acme", 1)


class TestDescribeReplacements:
    def test_has_entity_type_column_and_flags_drift(self):
        table = _sample_collection().describe_replacements()
        lines = table.splitlines()
        assert lines[1].split() == ["ENTITY", "TYPE", "ORIGINAL", "SYNTHETIC", "COUNT"]
        # Entity-type column leads each data row.
        assert any(line.startswith("ORGANIZATION") for line in lines)
        assert any(line.startswith("EMAIL_ADDRESS") for line in lines)
        # Lilly maps to two synthetics -> flagged.
        assert "1 original(s) map to >1 synthetic" in table
        assert any(line.rstrip().endswith("*") for line in lines)

    def test_empty_collection(self):
        assert _FakeCollection([]).describe_replacements() == (
            "No replacements found across the collection."
        )
