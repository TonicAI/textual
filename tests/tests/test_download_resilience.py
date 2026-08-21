from unittest.mock import Mock, patch

import pytest
import requests

from tonic_textual import __version__
from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.tonic_exception import TextualServerError


def _response(status_code: int, body: str, **headers: str) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = body.encode("utf-8")
    response.headers.update(headers)
    response.url = "https://textual.test/download"
    response.request = requests.Request("GET", response.url).prepare()
    return response


def _file(client: HttpClient) -> DatasetFile:
    return DatasetFile(
        client=client,
        id="file-id",
        dataset_id="dataset-id",
        name="file.pdf",
        num_rows=None,
        num_columns=0,
        processing_status="Completed",
        processing_error=None,
    )


def test_http_client_identifies_its_sdk_version() -> None:
    client = HttpClient("https://textual.test", "api-key", verify=True)

    assert client.headers["User-Agent"] == f"tonic-textual-python-sdk/{__version__}"


def test_http_get_file_preserves_non_json_server_error() -> None:
    session = Mock(spec=requests.Session)
    session.get.return_value = _response(
        500,
        "<html><h1>500 Internal Server Error</h1></html>",
        **{"Content-Type": "text/html"},
    )
    client = HttpClient("https://textual.test", "api-key", verify=True)

    with pytest.raises(TextualServerError, match="500 Internal Server Error"):
        client.http_get_file("/download", session)


@pytest.mark.parametrize(
    ("method_name", "requests_method"),
    [
        ("http_put", "put"),
        ("http_patch", "patch"),
        ("http_delete", "delete"),
    ],
)
def test_http_mutation_preserves_non_json_server_error(
    method_name: str,
    requests_method: str,
) -> None:
    response = _response(500, "<html><h1>500 Internal Server Error</h1></html>")
    client = HttpClient("https://textual.test", "api-key", verify=True)

    with (
        patch(f"tonic_textual.classes.httpclient.requests.{requests_method}", return_value=response),
        pytest.raises(TextualServerError, match="500 Internal Server Error") as error,
    ):
        getattr(client, method_name)("/resource")

    assert error.value.response is response


@pytest.mark.parametrize("status_code", [429, 502, 503, 504])
def test_dataset_file_download_retries_transient_http_errors(status_code: int) -> None:
    client = Mock(spec=HttpClient)
    transient_response = _response(status_code, "temporary upstream failure")
    transient_error = requests.HTTPError(response=transient_response)
    client.http_get_file.side_effect = [transient_error, b"redacted-pdf"]

    with patch("tonic_textual.classes.datasetfile.sleep") as sleep:
        result = _file(client).download(num_retries=2, wait_between_retries=3)

    assert result == b"redacted-pdf"
    sleep.assert_called_once_with(3)


def test_dataset_file_download_honors_retry_after() -> None:
    client = Mock(spec=HttpClient)
    transient_response = _response(
        429,
        "capacity exhausted",
        **{"Retry-After": "7"},
    )
    transient_error = requests.HTTPError(response=transient_response)
    client.http_get_file.side_effect = [transient_error, b"redacted-pdf"]

    with patch("tonic_textual.classes.datasetfile.sleep") as sleep:
        _file(client).download(num_retries=2, wait_between_retries=3)

    sleep.assert_called_once_with(7)


def test_dataset_file_download_reraises_transient_error_after_backoff_budget() -> None:
    client = Mock(spec=HttpClient)
    transient_response = _response(504, "temporary upstream failure")
    transient_error = requests.HTTPError(
        "504 Server Error: Gateway Timeout",
        response=transient_response,
    )
    client.http_get_file.side_effect = [
        transient_error,
        transient_error,
        transient_error,
    ]

    with (
        patch("tonic_textual.classes.datasetfile.sleep") as sleep,
        pytest.raises(requests.HTTPError, match="Gateway Timeout"),
    ):
        _file(client).download(num_retries=3, wait_between_retries=2)

    assert [call.args[0] for call in sleep.call_args_list] == [2, 4]


def test_dataset_file_download_does_not_retry_permanent_server_error() -> None:
    client = Mock(spec=HttpClient)
    client.http_get_file.side_effect = TextualServerError(
        {"error": "The PDF cannot be processed"}
    )

    with (
        patch("tonic_textual.classes.datasetfile.sleep") as sleep,
        pytest.raises(TextualServerError, match="PDF cannot be processed"),
    ):
        _file(client).download(num_retries=3, wait_between_retries=1)

    sleep.assert_not_called()
