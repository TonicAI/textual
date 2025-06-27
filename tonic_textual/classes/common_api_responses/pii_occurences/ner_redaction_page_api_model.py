from typing import Optional, Dict, List
import json

from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_api_model import NerRedactionApiModel

class NerRedactionPageApiModel(dict):
    def __init__(self, page_number: int, entities: List[NerRedactionApiModel], continuation_token: Optional[int] = None):
        self.page_number = page_number
        self.entities = entities
        self.continuation_token = continuation_token

        dict.__init__(
            self,
            page_number = page_number,
            enities = entities,
            continuation_token = continuation_token
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