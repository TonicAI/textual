import os
import uuid
from typing import Generator, List, Tuple

import boto3
import pytest
import requests
from dotenv import load_dotenv

from tests.utils.dataset_utils import wait_for_file_processing
from tests.utils.resource_utils import get_resource_path
from tonic_textual.audio_api import TextualAudio
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.parse_api import TonicTextualParse
from tonic_textual.redact_api import TonicTextual


def assert_spans_match_python_indices(s: str, spans: List[SingleDetectionResult]):
    """
    Check that spans correspond to the text they claim to represent.
    This is a basic validation that the spans are positioned correctly.
    """
    for x in spans:
        assert x["text"] == s[x["start"]: x["end"]]


@pytest.fixture(scope="session", autouse=True)
def load_env():
    # Load .env file from the directory where this file is located
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)


@pytest.fixture(scope="session")
def server_version() -> str:
    gh_actions = os.environ.get("GITHUB_ACTIONS")
    if gh_actions:
        return 'PRAPP'

    should_verify = True if os.environ.get("GITHUB_ACTIONS") == "true" else False
    with requests.Session() as session:
        res = session.get(os.environ["TEXTUAL_HOST"] + "/api/version", verify=should_verify)
        version = res.text

        if version.startswith('000-f'):
            return 'PRAPP'
        return version


@pytest.fixture(scope="module")
def textual():
    should_verify = True if os.environ.get("GITHUB_ACTIONS") == "true" else False
    return TonicTextual(
        base_url=os.environ["TEXTUAL_HOST"],
        api_key=os.environ["TEXTUAL_API_KEY"],
        verify=should_verify,
    )


@pytest.fixture(scope="module")
def textual_audio():
    should_verify = True if os.environ.get("GITHUB_ACTIONS") == "true" else False
    return TextualAudio(
        base_url=os.environ["TEXTUAL_HOST"],
        api_key=os.environ["TEXTUAL_API_KEY"],
        verify=should_verify,
    )


@pytest.fixture(scope="module")
def textual_parse():
    should_verify = True if os.environ.get("GITHUB_ACTIONS") == "true" else False
    return TonicTextualParse(
        os.environ["TEXTUAL_HOST"], os.environ["TEXTUAL_API_KEY"], verify=should_verify
    )


@pytest.fixture(scope="module")
def setup_bill_gates_txt_dataset(
        textual,
) -> Generator[Tuple[TonicTextual, str, str], None, None]:
    yield from setup_dataset(
        f"bill_gates-{uuid.uuid4()}",
        get_resource_path("William Henry Gates III (born Octob.txt"),
        textual,
    )


@pytest.fixture(scope="module")
def s3_boto_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ["S3_UPLOAD_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_UPLOAD_SECRET_KEY"],
        region_name=os.environ["AWS_DEFAULT_REGION"],
    )


def setup_dataset(
        dataset_name, dataset_path, textual
) -> Generator[Tuple[TonicTextual, str, str], None, None]:
    dataset = textual.create_dataset(dataset_name)
    dataset.add_file(dataset_path)
    wait_for_file_processing(textual, dataset_name)
    failed_files = textual.get_dataset(dataset_name).get_failed_files()
    assert len(failed_files) == 0, "Expected no failed files"
    yield textual, dataset_name, dataset_path
    # Will be executed after the last test
    textual.delete_dataset(dataset_name)
