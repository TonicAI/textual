from typing import Any, Dict, List, Optional, Union

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.entity_linking import (
    EntityLinkingEntity,
    EntityLinkingEdge,
    EntityLinkingResponseMixin,
    EntityLinkingScoreMatrix,
)


class LlmGrouping(dict):
    """Represents a group of related entities"""

    def __init__(
        self,
        representative: Optional[str],
        entities: List[Union[Replacement, EntityLinkingEntity]],
        pii_type: Optional[str] = None,
        entity_indices: Optional[List[int]] = None,
        linking_edges: Optional[List[EntityLinkingEdge]] = None,
    ):
        self.representative = representative
        self.entities = entities
        self.pii_type = pii_type
        self.entity_indices = entity_indices
        self.linking_edges = linking_edges

        dict.__init__(self, **self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "representative": self.representative,
            "entities": [e.to_dict() for e in self.entities]
        }
        if self.pii_type is not None:
            result["pii_type"] = self.pii_type
        if self.entity_indices is not None:
            result["entity_indices"] = self.entity_indices
        if self.linking_edges is not None:
            result["linking_edges"] = [edge.to_dict() for edge in self.linking_edges]
        return result


class GroupResponse(EntityLinkingResponseMixin, dict):
    """The response containing grouped entities.

    The optional score matrix is row-wise upper triangular. For entity indices
    ``i < j``, the corresponding score is at ``matrix[i][j - i - 1]``.
    """

    def __init__(
        self,
        groups: List[LlmGrouping],
        entities: Optional[List[EntityLinkingEntity]] = None,
        entity_linking_score_matrix: Optional[EntityLinkingScoreMatrix] = None,
    ):
        self.groups = groups
        self._include_entity_linking_entities = entities is not None
        self.entities = entities or []
        self.entity_linking_entities = self.entities
        self.entity_linking_groups = self.groups
        self.entity_linking_score_matrix = entity_linking_score_matrix

        dict.__init__(self, **self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "groups": [g.to_dict() for g in self.groups]
        }
        if self._include_entity_linking_entities:
            result["entities"] = [entity.to_dict() for entity in self.entities]
        if self.entity_linking_score_matrix is not None:
            result["entity_linking_score_matrix"] = [
                [score.to_dict() if score is not None else None for score in row]
                for row in self.entity_linking_score_matrix
            ]
        return result
