from typing import List
from tonic_textual.classes.dataset import Dataset
from urllib.parse import urlencode
import requests

from tonic_textual.generator_utils import convert_payload_to_generator_metadata, convert_payload_to_generator_config


class DatasetService:
    def __init__(self, client):
        self.client = client

    def get_dataset(self, dataset_name):
        with requests.Session() as session:
            params = {"datasetName": dataset_name}
            dataset = self.client.http_get(
                "/api/dataset/get_dataset_by_name?" + urlencode(params), session=session
            )

            return Dataset(
                self.client,
                dataset["id"],
                dataset["name"],
                dataset["files"],
                convert_payload_to_generator_config(dataset["generatorSetup"]),
                convert_payload_to_generator_metadata(dataset["generatorMetadata"]),
                dataset["labelBlockLists"],
                dataset["labelAllowLists"],
                dataset["docXImagePolicy"],
                dataset["docXCommentPolicy"],
                dataset["docXTablePolicy"],
                dataset["pdfSignaturePolicy"],
                dataset["pdfSynthModePolicy"],
            )

    def get_all_datasets(self) -> List[Dataset]:
        with requests.Session() as session:
            datasets = self.client.http_get("/api/dataset", session=session)

            return [
                Dataset(
                    self.client,
                    dataset["id"],
                    dataset["name"],
                    dataset["files"],
                    convert_payload_to_generator_config(dataset["generatorSetup"]),
                    convert_payload_to_generator_metadata(dataset["generatorMetadata"]),
                    dataset["labelBlockLists"],
                    dataset["labelAllowLists"],
                    dataset["docXImagePolicy"],
                    dataset["docXCommentPolicy"],
                    dataset["docXTablePolicy"],
                    dataset["pdfSignaturePolicy"],
                    dataset["pdfSynthModePolicy"],
                )
                for dataset in datasets
            ]
