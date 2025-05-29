from typing import List
from tonic_textual.classes.dataset import Dataset
from urllib.parse import urlencode
import requests

from tonic_textual.classes.enums.file_redaction_policies import docx_image_policy, docx_comment_policy, \
    docx_table_policy, pdf_signature_policy, pdf_synth_mode_policy
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

            # this is to mitigate a possible bug around a name change
            generator_metadata_raw = dataset.get("generatorMetadata")

            if generator_metadata_raw is None:
                generator_metadata_raw = dataset.get("datasetGeneratorMetadata")

            return Dataset(
                self.client,
                dataset["id"],
                dataset["name"],
                dataset["files"],
                convert_payload_to_generator_config(dataset.get("generatorSetup")),
                convert_payload_to_generator_metadata(dataset.get("datasetGeneratorMetadata")),
                dataset.get("labelBlockLists"),
                dataset.get("labelAllowLists"),
                dataset.get("docXImagePolicy", docx_image_policy.redact),
                dataset.get("docXCommentPolicy", docx_comment_policy.remove),
                dataset.get("docXTablePolicy", docx_table_policy.remove),
                dataset.get("pdfSignaturePolicy", pdf_signature_policy.redact),
                dataset.get("pdfSynthModePolicy", pdf_synth_mode_policy.V1),
            )

    def get_all_datasets(self) -> List[Dataset]:
        with requests.Session() as session:
            datasets = self.client.http_get("/api/dataset", session=session)

            return [
                self.get_dataset(dataset["name"])
                for dataset in datasets
            ]
