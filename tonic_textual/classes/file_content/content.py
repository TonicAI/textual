from typing import List, Dict, Optional
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.generator_utils import (
    filter_entities_by_config,
    make_utf_compatible_entities,
)

def create_empty_content() -> Dict:
    return {"text":"","hash":"1B2M2Y8AsgTpgAmY7PhCfg==","entities":[]}

class Content:
    def __init__(self, client: HttpClient, json_def: Optional[Dict]):
        
        if json_def is None:
            json_def = create_empty_content()
        
        self.entities: List[SingleDetectionResult] = [
            SingleDetectionResult(
                s["start"], s["end"], s["label"], s["text"], s["score"]
            )
            for s in json_def["entities"]
        ]
        self.hash = json_def["hash"]
        self.text = json_def["text"]
        self.client = client

    def get_markdown(self) -> str:
        return self.content

    def get_all_entities(self) -> List[SingleDetectionResult]:
        return self.entities

    def get_entities(self, entity_type_list: List[str]) -> List[SingleDetectionResult]:
        return [ent for ent in self.entities if ent["label"] in entity_type_list]

    def to_dict(self) -> Dict:
        return {
            "entities": [x.to_dict() for x in self.entities],
            "text": self.text,
            "hash": self.hash,
        }

    def redact(
        self,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Off,
    ) -> str:
        markdown = self.get_markdown()
        all_entities = self.get_all_entities()
        entities = filter_entities_by_config(
            all_entities, generator_config, generator_default
        )
        utf_compatible_entities = make_utf_compatible_entities(markdown, entities)
        response = self.client.http_post(
            "/api/redact/known_entities",
            data={"knownEntities": utf_compatible_entities, "text": markdown, "generatorConfig": generator_config, "generatorDefault": generator_default},
        )
        return response["redactedText"]

    def is_sensitive(self, sensitive_entity_types: List[str]):
        return len(self.get_entities(sensitive_entity_types)) > 0
