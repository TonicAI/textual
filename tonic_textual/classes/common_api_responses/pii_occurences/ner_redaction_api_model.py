import json
from typing import Dict

class NerRedactionApiModel(dict):
    def __init__(self, entity: str, head: str, tail: str):
        self.entity = entity,
        self.head = head
        self.tail = tail

        dict.__init__(
            self,
            head = head,
            tail = tail,
            entity = entity
        )
    
    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "page_number": self.page_number,
            "entities": self.entities,
            "continuation_token": self.continuation_token
        }
        return out