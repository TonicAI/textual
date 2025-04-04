import os
from typing import Generator, List, Tuple
import pytest
import uuid
import time
import boto3

from tonic_textual.parse_api import TonicTextualParse
from tonic_textual.redact_api import TonicTextual
from dotenv import load_dotenv
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)

from tests.utils.resource_utils import get_resource_path


def assert_spans_match_python_indices(s: str, spans: List[SingleDetectionResult]):
    """
    Check that spans correspond to the text they claim to represent.
    This is a basic validation that the spans are positioned correctly.
    """
    for x in spans:
        assert x["text"] == s[x["start"] : x["end"]]


def wait_for_file_processing(textual: TonicTextual, dataset_name: str):
    while True:
        dataset = textual.get_dataset(dataset_name)
        queued_files = dataset.get_queued_files()
        running_files = dataset.get_running_files()

        if not queued_files and not running_files:
            print("All files processed.")
            break
        time.sleep(5)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    # Load .env file from the directory where this file is located
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)


@pytest.fixture(scope="module")
def textual():
    should_verify = True if os.environ.get("GITHUB_ACTIONS") == "true" else False
    return TonicTextual(
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
def pipeline_with_files(textual_parse):
    return setup_pipeline(f"pipeline-{uuid.uuid4()}", textual_parse)


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


def setup_pipeline(pipeline_name, textual_parse):
    pipeline = textual_parse.create_local_pipeline(pipeline_name)

    files = [
        "multiple_sheets_multiple_cells_with_inline_strings.xlsx",
        "utterances_twocol.csv",
        "chat_transcript.txt",
        "Sample Invoice.pdf",
        "tonic_msa.docx",
    ]

    for file in files:
        with open(get_resource_path(file), "rb") as f:
            file_bytes = f.read()
            pipeline.add_file(file_bytes, file)

    # wait to make sure all files are processed.
    max_retries = 60
    while max_retries > 0:
        runs = pipeline.get_runs()
        successful_runs = list(filter(lambda r: r.status == "Completed", runs))
        if len(successful_runs) > 0:
            break
        else:
            print(f"Runs:{len(runs)}; Successful:{len(successful_runs)}")
        time.sleep(1)
        max_retries -= 1

    if max_retries == 0:
        raise Exception("Failed to process uploaded files")

    # we can remove this sleep later. right now we stop checking for status once 1 job has completed.
    # but depending on de-bounce times for local files the 5 files we upload may be spread across multiple jobs.
    # so we need to add logic to actual count total number of files processed.
    time.sleep(10)
    return pipeline
