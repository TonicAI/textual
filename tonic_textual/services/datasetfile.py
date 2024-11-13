from tonic_textual.classes.datasetfile import DatasetFile
from typing import List
import requests


class DatasetFileService:
    def __init__(self, client):
        self.client = client

    def get_files(self, dataset_id: str) -> List[DatasetFile]:
        with requests.Session() as session:
            dataset = self.client.http_get(
                f"/api/dataset/{dataset_id}", session=session
            )
            return [
                DatasetFile(
                    self.client,
                    f["fileId"],
                    dataset_id,
                    f["fileName"],
                    f.get("numRows"),
                    f["numColumns"],
                    f["processingStatus"],
                    f.get("processingError"),
                    f.get("labelAllowLists"),
                )
                for f in dataset["files"]
            ]
