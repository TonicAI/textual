from typing import List, Optional

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.entity_linking import (
    EntityLinkingEntity,
    EntityLinkingResponseMixin,
    EntityLinkingScoreMatrix,
)
from tonic_textual.classes.llm_synthesis.llm_grouping_models import LlmGrouping


class RedactionResponse(EntityLinkingResponseMixin, dict):
    """Redaction response object

    Attributes
    ----------
    original_text : str
        The original text.
    redacted_text : str
        The redacted and synthesized text.
    usage : int
        The number of words used
    de_identify_results : List[Replacement]
        The list of named entities that were found in original_text.
    entity_linking_entities : List[EntityLinkingEntity]
        The entities indexed by the linking groups and score matrix.
    entity_linking_groups : List[LlmGrouping]
        The groups produced by entity linking.
    entity_linking_score_matrix : Optional[EntityLinkingScoreMatrix]
        A symmetric matrix of pairwise linking scores, when requested.
    """

    def __init__(
        self,
        original_text: str,
        redacted_text: str,
        usage: int,
        de_identify_results: List[Replacement],
        entity_linking_entities: Optional[List[EntityLinkingEntity]] = None,
        entity_linking_groups: Optional[List[LlmGrouping]] = None,
        entity_linking_score_matrix: Optional[EntityLinkingScoreMatrix] = None,
    ):
        self.original_text = original_text
        self.redacted_text = redacted_text
        self.usage = usage
        self.de_identify_results = de_identify_results
        self.entity_linking_entities = entity_linking_entities or []
        self.entity_linking_groups = entity_linking_groups or []
        self.entity_linking_score_matrix = entity_linking_score_matrix

        response = dict(
            original_text=original_text,
            redacted_text=redacted_text,
            usage=usage,
            de_identify_results=de_identify_results,
        )
        if entity_linking_entities is not None:
            response["entity_linking_entities"] = [
                entity.to_dict() for entity in self.entity_linking_entities
            ]
            response["entity_linking_groups"] = [
                group.to_dict() for group in self.entity_linking_groups
            ]
        if entity_linking_score_matrix is not None:
            response["entity_linking_score_matrix"] = [
                [score.to_dict() if score is not None else None for score in row]
                for row in entity_linking_score_matrix
            ]
        dict.__init__(self, **response)

    def describe(self) -> str:
        result = f"{self.redacted_text}\n"
        for x in self.de_identify_results:
            result += f"{x.describe()}\n"
        return result

    def get_usage(self):
        return self.usage
