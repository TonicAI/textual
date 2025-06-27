from typing import List, Dict
import json

from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_page_api_model import NerRedactionPageApiModel

class PiiOccurrenceResponse(dict):
    def __init__(self, id: str, file_name: str, pages: List[NerRedactionPageApiModel]):
        self.id = id
        self.file_name=file_name
        self.pages = pages

        dict.__init__(
            self,
            id = id,
            file_name = file_name,
            pages = pages
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "id": self.id,
            "file_name": self.file_name,
            "pages": self.pages,            
        }
        return out