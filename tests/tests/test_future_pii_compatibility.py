import pytest

from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.generator_utils import (
    ServerSuppliedPiiDict,
    convert_payload_to_generator_config,
    validate_generator_default_and_config,
    validate_generator_metadata,
)


FUTURE_PII_TYPE = "FUTURE_SOLAR_PII_TYPE"


class RequestCaptured(Exception):
    pass


class RecordingHttpClient:
    def __init__(self):
        self.request_data = None

    def http_put(self, _path, data):
        self.request_data = data
        raise RequestCaptured


def test_dataset_edit_forwards_future_server_pii_types():
    client = RecordingHttpClient()
    generator_config = convert_payload_to_generator_config(
        {FUTURE_PII_TYPE: PiiState.Redaction.value}
    )
    dataset = Dataset(
        client,
        "source-dataset",
        "source",
        [],
        [],
        generator_config=generator_config,
        generator_metadata={},
        label_block_lists={},
        label_allow_lists={},
    )

    with pytest.raises(RequestCaptured):
        dataset.edit(generator_config=dataset.generator_config.copy())

    assert client.request_data["generatorSetup"] == {
        FUTURE_PII_TYPE: PiiState.Redaction.value
    }


def test_server_supplied_future_metadata_is_valid_for_copying():
    generator_metadata = ServerSuppliedPiiDict(
        {FUTURE_PII_TYPE: BaseMetadata()},
        server_supplied_pii_types=[FUTURE_PII_TYPE],
    )

    validate_generator_metadata(
        generator_metadata,
        additional_pii_types=generator_metadata.server_supplied_pii_types,
    )


def test_unknown_caller_supplied_pii_type_is_still_rejected():
    with pytest.raises(Exception, match="Invalid key for generator config"):
        validate_generator_default_and_config(
            PiiState.Redaction,
            {FUTURE_PII_TYPE: PiiState.Redaction},
        )
