import json

from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.common_api_responses.dataset_entity_mappings_response import (
    DatasetEntityMappingsResponse,
)


class RecordingClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def http_get(self, url, session, params={}):
        self.calls.append({"url": url, "session": session, "params": params})
        return self.response


def create_dataset(client) -> Dataset:
    return Dataset(
        client=client,
        id="dataset-123",
        name="customers",
        files=[],
        custom_pii_entity_ids=[],
        generator_config={},
        generator_metadata={},
        label_block_lists={},
        label_allow_lists={},
    )


def test_get_entity_mappings_calls_dataset_endpoint_and_parses_response():
    client = RecordingClient(
        {
            "files": [
                {
                    "fileId": "file-1",
                    "fileName": "customers.csv",
                    "entities": [
                        {
                            "label": "NAME_GIVEN",
                            "text": "John",
                            "redactedText": "[NAME_GIVEN_18e87]",
                            "syntheticText": "Ladawn",
                            "appliedGeneratorState": "Synthesis",
                            "outputText": "Ladawn",
                            "rowNumber": 12,
                            "columnIndex": 1,
                            "score": 0.99,
                        }
                    ],
                },
                {
                    "fileId": "file-2",
                    "fileName": "notes.txt",
                    "entities": [],
                },
            ]
        }
    )
    dataset = create_dataset(client)

    response = dataset.get_entity_mappings()

    assert client.calls[0]["url"] == "/api/dataset/dataset-123/entity_mappings"
    assert isinstance(response, DatasetEntityMappingsResponse)
    assert len(response.files) == 2

    first_file = response.files[0]
    assert first_file.file_id == "file-1"
    assert first_file.file_name == "customers.csv"
    assert len(first_file.entities) == 1

    first_entity = first_file.entities[0]
    assert first_entity.label == "NAME_GIVEN"
    assert first_entity.text == "John"
    assert first_entity.redacted_text == "[NAME_GIVEN_18e87]"
    assert first_entity.synthetic_text == "Ladawn"
    assert first_entity.applied_generator_state == "Synthesis"
    assert first_entity.output_text == "Ladawn"
    assert first_entity.row_number == 12
    assert first_entity.column_index == 1
    assert first_entity.score == 0.99

    assert response.files[1].entities == []


def test_dataset_entity_mappings_response_is_json_serializable():
    client = RecordingClient(
        {
            "files": [
                {
                    "fileId": "file-1",
                    "fileName": "customers.csv",
                    "entities": [
                        {
                            "label": "EMAIL_ADDRESS",
                            "text": "john@example.com",
                            "redactedText": "[EMAIL_ADDRESS_ctc90]",
                            "appliedGeneratorState": "Redaction",
                            "outputText": "[EMAIL_ADDRESS_ctc90]",
                            "score": 0.97,
                        }
                    ],
                }
            ]
        }
    )
    dataset = create_dataset(client)

    response = dataset.get_entity_mappings()

    payload = json.loads(json.dumps(response))
    assert payload == {
        "files": [
            {
                "file_id": "file-1",
                "file_name": "customers.csv",
                "entities": [
                    {
                        "label": "EMAIL_ADDRESS",
                        "text": "john@example.com",
                        "redacted_text": "[EMAIL_ADDRESS_ctc90]",
                        "applied_generator_state": "Redaction",
                        "output_text": "[EMAIL_ADDRESS_ctc90]",
                        "score": 0.97,
                    }
                ],
            }
        ]
    }
