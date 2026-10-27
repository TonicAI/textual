import pytest

from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.enums.file_type import FileTypeEnum
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.generator_utils import (
    convert_payload_to_generator_config,
    filter_entities_by_config,
    generate_redact_payload,
    make_utf_compatible_entities,
    validate_generator_default_and_config,
    validate_generator_metadata,
)
from tonic_textual.redact_api import TextualNer


PARENT = "CUSTOM_TREATMENT_DETAILS"
CONDITION_KEY = f"{PARENT}:MEDICAL_CONDITION"


def _detection(label, model_based_entity_name=None, start=0, end=4):
    return SingleDetectionResult(
        start,
        end,
        label,
        "text",
        0.9,
        model_based_entity_name=model_based_entity_name,
    )


class RecordingClient:
    def __init__(self, response=None):
        self.requests = []
        self.response = response

    def http_post(self, path, data=None, **_):
        self.requests.append((path, data))
        return self.response

    def http_put(self, path, data):
        self.requests.append((path, data))
        raise RequestCaptured


class RequestCaptured(Exception):
    pass


def test_combined_key_is_valid_when_parent_is_a_custom_entity():
    validate_generator_default_and_config(
        PiiState.Redaction,
        {PARENT: PiiState.Off, CONDITION_KEY: PiiState.Redaction},
        custom_entities=[PARENT],
    )


def test_combined_key_parent_matches_custom_entities_case_insensitively():
    validate_generator_default_and_config(
        PiiState.Redaction,
        {"custom_treatment_details:medical_condition": "redaction"},
        custom_entities=[PARENT],
    )


def test_combined_key_without_custom_entity_is_rejected():
    with pytest.raises(Exception, match=f"requires '{PARENT}' to be listed in custom_entities"):
        validate_generator_default_and_config(
            PiiState.Redaction,
            {CONDITION_KEY: PiiState.Redaction},
        )


def test_combined_key_for_a_different_custom_entity_is_rejected():
    with pytest.raises(Exception, match=f"requires '{PARENT}' to be listed in custom_entities"):
        validate_generator_default_and_config(
            PiiState.Redaction,
            {CONDITION_KEY: PiiState.Redaction},
            custom_entities=["CUSTOM_OTHER_MODEL"],
        )


@pytest.mark.parametrize("label", ["", "1CONDITION", "MEDICAL-CONDITION", "A" * 65, "A:B"])
def test_combined_key_with_invalid_label_is_rejected(label):
    with pytest.raises(Exception, match="is not a valid label"):
        validate_generator_default_and_config(
            PiiState.Redaction,
            {f"{PARENT}:{label}": PiiState.Redaction},
            custom_entities=[PARENT],
        )


def test_combined_key_with_longest_valid_label_is_accepted():
    validate_generator_default_and_config(
        PiiState.Redaction,
        {f"{PARENT}:A{'_' * 63}": PiiState.Redaction},
        custom_entities=[PARENT],
    )


def test_combined_key_is_not_valid_generator_metadata():
    with pytest.raises(Exception, match="Invalid key for generator metadata"):
        validate_generator_metadata(
            {CONDITION_KEY: BaseMetadata()},
            custom_entities=[PARENT],
        )


def test_redact_payload_forwards_combined_key_with_uppercased_label():
    payload = generate_redact_payload(
        generator_config={PARENT: "off", f"{PARENT}:medical_condition": "redaction"},
        custom_entities=[PARENT],
    )

    assert payload["generatorConfig"] == {
        PARENT: "Off",
        CONDITION_KEY: "Redaction",
    }
    assert payload["customPiiEntityIds"] == [PARENT]


def test_filter_prefers_combined_key_over_parent_key():
    condition = _detection("MEDICAL_CONDITION", PARENT)
    medication = _detection("MEDICATION", PARENT)

    filtered = filter_entities_by_config(
        [condition, medication],
        {PARENT: PiiState.Off, CONDITION_KEY: PiiState.Redaction},
        PiiState.Redaction,
    )

    assert filtered == [condition]


def test_filter_falls_back_to_parent_key():
    condition = _detection("MEDICAL_CONDITION", PARENT)
    medication = _detection("MEDICATION", PARENT)

    filtered = filter_entities_by_config(
        [condition, medication],
        {PARENT: PiiState.Redaction, CONDITION_KEY: PiiState.Off},
        PiiState.Off,
    )

    assert filtered == [medication]


def test_filter_falls_back_to_label_and_default_without_parent_settings():
    condition = _detection("MEDICAL_CONDITION", PARENT)
    medication = _detection("MEDICATION", PARENT)
    name = _detection("NAME_GIVEN")

    filtered = filter_entities_by_config(
        [condition, medication, name],
        {"MEDICATION": PiiState.Redaction, "NAME_GIVEN": PiiState.Redaction},
        PiiState.Off,
    )

    assert filtered == [medication, name]


def test_filter_matches_combined_key_case_insensitively():
    condition = _detection("MEDICAL_CONDITION", PARENT)

    assert filter_entities_by_config(
        [condition],
        {"custom_treatment_details:medical_condition": "off"},
        "redaction",
    ) == []


def test_combined_key_does_not_apply_to_another_models_label():
    condition = _detection("MEDICAL_CONDITION", "CUSTOM_OTHER_MODEL")

    assert filter_entities_by_config(
        [condition],
        {CONDITION_KEY: PiiState.Off},
        PiiState.Redaction,
    ) == [condition]


def test_detection_serializes_model_based_entity_name():
    detection = _detection("MEDICAL_CONDITION", PARENT)

    assert detection["model_based_entity_name"] == PARENT
    assert detection.to_dict()["modelBasedEntityName"] == PARENT
    assert make_utf_compatible_entities("text", [detection])[0]["modelBasedEntityName"] == PARENT


def test_detection_omits_model_based_entity_name_when_absent():
    detection = _detection("NAME_GIVEN")

    assert "model_based_entity_name" not in detection
    assert "modelBasedEntityName" not in detection.to_dict()


def test_parsed_file_markdown_resolves_combined_key_and_forwards_parent():
    client = RecordingClient({"redactedText": "[MEDICAL_CONDITION] and aspirin"})
    file_keys = [
        "id", "userId", "oid", "fileSizeInKb", "fileName", "escapeChar", "quoteChar",
        "hasHeader", "delimiter", "nullChar", "numRows", "columnCount", "wordCount",
        "redactedWordCount", "createdDate", "lastModifiedDate", "fileHash",
        "fileSource", "filePath",
    ]
    content = {
        "text": "flu and aspirin",
        "hash": "hash",
        "entities": [
            {
                "start": 0,
                "end": 3,
                "label": "MEDICAL_CONDITION",
                "text": "flu",
                "score": 0.9,
                "modelBasedEntityName": PARENT,
            },
            {
                "start": 8,
                "end": 15,
                "label": "MEDICATION",
                "text": "aspirin",
                "score": 0.9,
                "modelBasedEntityName": PARENT,
            },
        ],
    }
    parse_result = FileParseResult(
        {
            "id": "parse-id",
            "file": {**dict.fromkeys(file_keys), "fileType": FileTypeEnum.raw},
            "parsedFilePath": "parsed",
            "createdDate": None,
            "lastModifiedDate": None,
        },
        client,
        document={"content": content},
    )

    parse_result.get_markdown(
        generator_config={PARENT: "Off", CONDITION_KEY: "Redaction"},
        generator_default="Redaction",
    )

    path, request = client.requests[0]
    assert path == "/api/redact/known_entities"
    assert [
        (entity["label"], entity["modelBasedEntityName"])
        for entity in request["knownEntities"]
    ] == [("MEDICAL_CONDITION", PARENT)]


def test_dataset_edit_forwards_server_supplied_combined_key():
    client = RecordingClient()
    generator_config = convert_payload_to_generator_config(
        {PARENT: "Off", CONDITION_KEY: "Redaction"}
    )
    dataset = Dataset(
        client,
        "dataset-id",
        "dataset",
        [],
        [],
        generator_config=generator_config,
        generator_metadata={},
        label_block_lists={},
        label_allow_lists={},
    )

    with pytest.raises(RequestCaptured):
        dataset.edit(generator_config=dataset.generator_config.copy())

    _, request = client.requests[0]
    assert request["generatorSetup"] == {PARENT: "Off", CONDITION_KEY: "Redaction"}


def _dataset_with_server_config(client, payload):
    return Dataset(
        client,
        "dataset-id",
        "dataset",
        [],
        [],
        generator_config=convert_payload_to_generator_config(payload),
        generator_metadata={},
        label_block_lists={},
        label_allow_lists={},
    )


def test_dataset_edit_accepts_new_combined_key_for_enabled_custom_entity():
    client = RecordingClient()
    dataset = _dataset_with_server_config(client, {PARENT: "Off"})
    generator_config = dataset.generator_config.copy()
    generator_config[f"{PARENT}:medical_condition"] = PiiState.Redaction

    with pytest.raises(RequestCaptured):
        dataset.edit(generator_config=generator_config)

    _, request = client.requests[0]
    assert request["generatorSetup"] == {PARENT: "Off", CONDITION_KEY: "Redaction"}


def test_dataset_edit_rejects_combined_key_for_custom_entity_not_on_dataset():
    client = RecordingClient()
    dataset = _dataset_with_server_config(client, {PARENT: "Off"})
    generator_config = dataset.generator_config.copy()
    generator_config["CUSTOM_OTHER_MODEL:MEDICAL_CONDITION"] = PiiState.Redaction

    with pytest.raises(
        Exception,
        match="requires 'CUSTOM_OTHER_MODEL' to be a custom entity that is enabled on the dataset",
    ):
        dataset.edit(generator_config=generator_config)

    assert client.requests == []


def test_dataset_edit_matches_combined_key_parent_case_sensitively():
    client = RecordingClient()
    dataset = _dataset_with_server_config(client, {PARENT: "Off"})
    generator_config = dataset.generator_config.copy()
    generator_config[f"{PARENT.lower()}:MEDICAL_CONDITION"] = PiiState.Redaction

    with pytest.raises(Exception, match="to be a custom entity that is enabled on the dataset"):
        dataset.edit(generator_config=generator_config)


def test_dataset_edit_rejects_combined_key_without_server_supplied_config():
    client = RecordingClient()
    dataset = _dataset_with_server_config(client, {})

    with pytest.raises(Exception, match="to be a custom entity that is enabled on the dataset"):
        dataset.edit(generator_config={CONDITION_KEY: PiiState.Redaction})


def test_dataset_edit_rejects_combined_key_with_invalid_label():
    client = RecordingClient()
    dataset = _dataset_with_server_config(client, {PARENT: "Off"})
    generator_config = dataset.generator_config.copy()
    generator_config[f"{PARENT}:1CONDITION"] = PiiState.Redaction

    with pytest.raises(Exception, match="is not a valid label"):
        dataset.edit(generator_config=generator_config)


class ActiveEntitiesClient:
    def __init__(self, entities):
        self.paths = []
        self.entities = entities

    def http_get(self, path, session=None, params=None):
        self.paths.append(path)
        return {"entities": self.entities}


def _textual(entities):
    textual = TextualNer(api_key="test")
    client = ActiveEntitiesClient(entities)
    textual.model_entity_service.client = client
    return textual, client


def test_custom_entity_labels_come_from_the_active_entity_list():
    textual, client = _textual(
        [
            {"name": "CUSTOM_OTHER", "entityLabels": ["OTHER_LABEL"]},
            {"name": PARENT, "entityLabels": ["DOSE", "MEDICAL_CONDITION"]},
        ]
    )

    assert textual.get_custom_entity_labels(PARENT) == ["DOSE", "MEDICAL_CONDITION"]
    assert client.paths == ["/api/model-based-entities/active"]


def test_custom_entity_labels_match_the_name_case_insensitively():
    textual, _ = _textual([{"name": PARENT, "entityLabels": ["DOSE"]}])

    assert textual.get_custom_entity_labels(PARENT.lower()) == ["DOSE"]


def test_custom_entity_labels_are_empty_for_a_single_label_model():
    textual, _ = _textual([{"name": PARENT, "entityLabels": []}])

    assert textual.get_custom_entity_labels(PARENT) == []


def test_custom_entity_labels_are_empty_when_the_server_does_not_report_them():
    textual, _ = _textual([{"name": PARENT}])

    assert textual.get_custom_entity_labels(PARENT) == []


def test_custom_entity_labels_reject_an_inactive_custom_entity():
    textual, _ = _textual([{"name": "CUSTOM_OTHER", "entityLabels": []}])

    with pytest.raises(ValueError, match=f"'{PARENT}' is not an active custom entity type"):
        textual.get_custom_entity_labels(PARENT)
