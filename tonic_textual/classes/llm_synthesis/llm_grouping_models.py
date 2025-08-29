from dataclasses import dataclass
from typing import List

from tonic_textual.classes.common_api_responses.replacement import Replacement

@dataclass
class LlmGrouping:
    """Represents a group of related entities"""
    representative: str
    entities: List[Replacement]

@dataclass
class GroupResponse:
    """The response containing grouped entities"""
    groups: List[LlmGrouping]