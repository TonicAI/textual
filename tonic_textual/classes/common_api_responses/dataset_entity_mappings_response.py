import json
from typing import Dict, List

from tonic_textual.classes.common_api_responses.dataset_file_entity_mappings import (
    DatasetFileEntityMappings,
)


class DatasetEntityMappingsResponse(dict):
    """Entity mappings for a dataset, grouped by file.

    Attributes
    ----------
    files : List[DatasetFileEntityMappings]
        The entity mappings for the dataset, grouped by file.
    """

    def __init__(self, files: List[DatasetFileEntityMappings]):
        self.files = files

        dict.__init__(
            self,
            files=files,
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "DatasetEntityMappingsResponse":
        return cls(
            files=[
                DatasetFileEntityMappings.from_dict(file_data)
                for file_data in data["files"]
            ]
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        return {
            "files": [file.to_dict() for file in self.files],
        }
