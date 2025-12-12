from typing import Any, Dict, List

from tonic_textual.classes.common_api_responses.replacement import Replacement


class LlmGrouping(dict):
    """Represents a group of related entities"""

    def __init__(self, representative: str, entities: List[Replacement]):
        self.representative = representative
        self.entities = entities

        dict.__init__(
            self,
            representative=representative,
            entities=[e.to_dict() for e in entities]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "representative": self.representative,
            "entities": [e.to_dict() for e in self.entities]
        }


class GroupResponse(dict):
    """The response containing grouped entities"""

    def __init__(self, groups: List[LlmGrouping]):
        self.groups = groups

        dict.__init__(
            self,
            groups=[g.to_dict() for g in groups]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "groups": [g.to_dict() for g in self.groups]
        }
