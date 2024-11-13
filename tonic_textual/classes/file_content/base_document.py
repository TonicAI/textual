from typing import Dict, List
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.httpclient import HttpClient


class BaseDocument:
    def __init__(self, client: HttpClient, json_def: Dict):
        self.client = client
        self._json_def = json_def
        self.markdown = json_def["content"]["text"]
        self.entities: List[SingleDetectionResult] = [
            SingleDetectionResult(
                s["start"], s["end"], s["label"], s["text"], s["score"]
            )
            for s in json_def["content"]["entities"]
        ]
        self.schema_version = json_def.get("schemaVersion", 0)

    def get_markdown(self):
        return self.markdown

    def get_all_entities(self):
        return self.entities

    def get_json(self) -> Dict:
        return self._json_def

    def to_dict(self):
        return self._json_def
