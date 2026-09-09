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


@dataclass(frozen=True)
class EntityLinkingEdge:
    """One direct edge in a group's maximum spanning tree."""

    entity_index_a: int
    entity_index_b: int
    confidence: float
    confidence_type: str

    @classmethod
    def from_api(cls, edge: Dict[str, Any]) -> "EntityLinkingEdge":
        return cls(
            entity_index_a=edge["entityIndexA"],
            entity_index_b=edge["entityIndexB"],
            confidence=edge["linkingConfidence"],
            confidence_type=edge["linkingConfidenceType"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_index_a": self.entity_index_a,
            "entity_index_b": self.entity_index_b,
            "linking_confidence": self.confidence,
            "linking_confidence_type": self.confidence_type,
        }


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
    entity_linking_groups: List[Any]
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

    def split_entity_linking_groups(
        self,
        min_confidence: float,
    ) -> List[List[EntityLinkingEntity]]:
        """Split existing groups by removing MST edges below the threshold."""

        split_groups = []
        for group in self.entity_linking_groups:
            if group.entity_indices is None or group.linking_edges is None:
                raise ValueError(
                    "Entity-linking edges were not requested; set "
                    "include_entity_linking_scores=True"
                )

            neighbors = {index: [] for index in group.entity_indices}
            for edge in group.linking_edges:
                if edge.confidence < min_confidence:
                    continue
                neighbors[edge.entity_index_a].append(edge.entity_index_b)
                neighbors[edge.entity_index_b].append(edge.entity_index_a)

            visited = set()
            group_order = {
                entity_index: position
                for position, entity_index in enumerate(group.entity_indices)
            }
            for start in group.entity_indices:
                if start in visited:
                    continue

                pending = [start]
                component_indices = []
                visited.add(start)
                while pending:
                    entity_index = pending.pop()
                    component_indices.append(entity_index)
                    for neighbor in neighbors[entity_index]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            pending.append(neighbor)

                component_indices.sort(key=group_order.__getitem__)
                split_groups.append([
                    self.entity_linking_entities[index]
                    for index in component_indices
                ])

        return split_groups
