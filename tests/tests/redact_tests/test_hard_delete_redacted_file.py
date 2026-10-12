"""Unit tests for TextualNer.hard_delete_redacted_file. These do not require a running Textual server."""

from unittest.mock import patch

import pytest
import requests

from tonic_textual.classes.tonic_exception import FileNotReadyForDeletion
from tonic_textual.redact_api import TextualNer


def _response(status_code: int) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = b""
    response.url = "http://localhost/api/unattachedfile/job-id"
    response.request = requests.Request("DELETE", response.url).prepare()
    return response


@pytest.fixture
def ner():
    return TextualNer("http://localhost", api_key="fake-key")


def test_sends_delete_for_job(ner):
    with patch("tonic_textual.classes.httpclient.requests.delete", return_value=_response(204)) as delete:
        assert ner.hard_delete_redacted_file("job-id") is None

    assert delete.call_args.args[0] == "http://localhost/api/unattachedfile/job-id"


def test_still_processing_raises_file_not_ready_for_deletion(ner):
    with (
        patch("tonic_textual.classes.httpclient.requests.delete", return_value=_response(409)),
        pytest.raises(FileNotReadyForDeletion),
    ):
        ner.hard_delete_redacted_file("job-id")


def test_unknown_job_raises_http_error(ner):
    with (
        patch("tonic_textual.classes.httpclient.requests.delete", return_value=_response(404)),
        pytest.raises(requests.exceptions.HTTPError) as error,
    ):
        ner.hard_delete_redacted_file("job-id")

    assert error.value.response.status_code == 404
