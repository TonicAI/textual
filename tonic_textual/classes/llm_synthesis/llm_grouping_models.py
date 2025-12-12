from dataclasses import dataclass
from typing import Any, Dict, List

from tonic_textual.classes.common_api_responses.replacement import Replacement

@dataclass
class LlmGrouping:
    """Represents a group of related entities"""
    representative: str
    entities: List[Replacement]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "representative": self.representative,
            "entities": [e.to_dict() for e in self.entities]
        }

@dataclass
class GroupResponse:
    """The response containing grouped entities"""
    groups: List[LlmGrouping]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "groups": [g.to_dict() for g in self.groups]
        }