import json
from typing import Dict, List

from tonic_textual.classes.common_api_responses.entity_mapping import EntityMapping


class DatasetFileEntityMappings(dict):
    """The entity mappings detected for a single dataset file.

    Attributes
    ----------
    file_id : str
        The identifier of the dataset file.
    file_name : str
        The file name shown in the dataset.
    entities : List[EntityMapping]
        The entity mappings detected for this file after the dataset generator
        configuration is applied.
    """

    def __init__(
        self,
        file_id: str,
        file_name: str,
        entities: List[EntityMapping],
    ):
        self.file_id = file_id
        self.file_name = file_name
        self.entities = entities

        dict.__init__(
            self,
            file_id=file_id,
            file_name=file_name,
            entities=entities,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "DatasetFileEntityMappings":
        return cls(
            file_id=data["fileId"],
            file_name=data["fileName"],
            entities=[EntityMapping.from_dict(entity) for entity in data["entities"]],
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        return {
            "file_id": self.file_id,
            "file_name": self.file_name,
            "entities": [entity.to_dict() for entity in self.entities],
        }
