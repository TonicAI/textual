from tonic_textual.classes.dataset import Dataset
from urllib.parse import urlencode
import requests


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
                dataset["generatorSetup"],
                dataset["labelBlockLists"],
                dataset["labelAllowLists"],
            )
