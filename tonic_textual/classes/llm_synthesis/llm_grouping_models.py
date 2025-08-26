from dataclasses import dataclass
from typing import List

from tonic_textual.classes.common_api_responses.ner_entity import NerEntity

# Assuming these types are defined elsewhere
# from your_module import NerEntity, PiiTypeEnum

@dataclass
class GroupRequest:
    """The request for grouping entities"""
    entities: List[NerEntity]  # The list of entities to group
    original_text: str  # The original text where the entities were found

@dataclass
class LlmGrouping:
    """Represents a group of related entities"""
    representative: str
    entities: List[NerEntity]

@dataclass
class GroupResponse:
    """The response containing grouped entities"""
    groups: List[LlmGrouping]