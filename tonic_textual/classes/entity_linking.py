from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional


@dataclass(frozen=True)
class EntityLinkingEntity:
    """An entity included in an entity-linking response."""

    start: int
    end: int
    python_start: int
    python_end: int
    label: str
    text: str
    score: float
    language: Optional[str] = None
    example_redaction: Optional[str] = None

    @classmethod
    def from_api(cls, entity: Dict[str, Any]) -> "EntityLinkingEntity":
        return cls(
            start=entity["start"],
            end=entity["end"],
            python_start=entity.get("pythonStart", entity["start"]),
            python_end=entity.get("pythonEnd", entity["end"]),
            label=entity["label"],
            text=entity["text"],
            score=entity["score"],
            language=entity.get("language"),
            example_redaction=entity.get("exampleRedaction"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "python_start": self.python_start,
            "python_end": self.python_end,
            "label": self.label,
            "text": self.text,
            "score": self.score,
            "language": self.language,
            "example_redaction": self.example_redaction,
        }


@dataclass(frozen=True)
class EntityLinkingScore:
    """The confidence and provenance for one entity-linking matrix cell."""

    confidence: float
    confidence_type: str

    @classmethod
    def from_api(cls, score: Dict[str, Any]) -> "EntityLinkingScore":
        return cls(
            confidence=score["linkingConfidence"],
            confidence_type=score["linkingConfidenceType"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "linking_confidence": self.confidence,
            "linking_confidence_type": self.confidence_type,
        }


@dataclass(frozen=True)
class EntityLink:
    """A scored link between two entities."""

    entity_a: EntityLinkingEntity
    entity_b: EntityLinkingEntity
    confidence: float
    confidence_type: str


EntityLinkingScoreMatrix = List[List[Optional[EntityLinkingScore]]]


def parse_entity_linking_score_matrix(
    matrix: Optional[List[List[Optional[Dict[str, Any]]]]],
) -> Optional[EntityLinkingScoreMatrix]:
    if matrix is None:
        return None

    return [
        [EntityLinkingScore.from_api(cell) if cell is not None else None for cell in row]
        for row in matrix
    ]


class EntityLinkingResponseMixin:
    entity_linking_entities: List[EntityLinkingEntity]
    entity_linking_score_matrix: Optional[EntityLinkingScoreMatrix]

    def iter_entity_links(
        self,
        min_confidence: float = 0.0,
        confidence_type: Optional[str] = None,
    ) -> Iterator[EntityLink]:
        """Yield each unique matrix link that matches the supplied filters."""

        if self.entity_linking_score_matrix is None:
            return

        for entity_index, row in enumerate(self.entity_linking_score_matrix):
            for linked_entity_index in range(entity_index + 1, len(row)):
                score = row[linked_entity_index]
                if score is None or score.confidence < min_confidence:
                    continue
                if confidence_type is not None and score.confidence_type != confidence_type:
                    continue

                yield EntityLink(
                    entity_a=self.entity_linking_entities[entity_index],
                    entity_b=self.entity_linking_entities[linked_entity_index],
                    confidence=score.confidence,
                    confidence_type=score.confidence_type,
                )
