from unittest.mock import Mock

import pytest
import requests

from tonic_textual.services.dataset import DatasetService


def dataset_summary(name: str, viewable: bool = True) -> dict:
    return {
        "name": name,
        "operations": ["ViewSettings"] if viewable else [],
    }


def dataset_details(name: str) -> dict:
    return {
        "id": f"{name}-id",
        "name": name,
        "files": [],
        "customPiiEntityIds": [],
        "labelBlockLists": {},
        "labelAllowLists": {},
    }


def http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)


def test_get_all_datasets_skips_dataset_deleted_after_listing():
    client = Mock()
    client.http_get.side_effect = [
        [
            dataset_summary("surviving-one"),
            dataset_summary("deleted"),
            dataset_summary("hidden", viewable=False),
            dataset_summary("surviving-two"),
        ],
        dataset_details("surviving-one"),
        http_error(404),
        dataset_details("surviving-two"),
    ]

    datasets = DatasetService(client).get_all_datasets()

    assert [dataset.name for dataset in datasets] == [
        "surviving-one",
        "surviving-two",
    ]
    assert client.http_get.call_count == 4


def test_get_all_datasets_propagates_non_not_found_errors():
    forbidden = http_error(403)
    client = Mock()
    client.http_get.side_effect = [
        [dataset_summary("forbidden")],
        forbidden,
    ]

    with pytest.raises(requests.HTTPError) as raised:
        DatasetService(client).get_all_datasets()

    assert raised.value is forbidden


def test_get_dataset_propagates_not_found():
    not_found = http_error(404)
    client = Mock()
    client.http_get.side_effect = not_found

    with pytest.raises(requests.HTTPError) as raised:
        DatasetService(client).get_dataset("deleted")

    assert raised.value is not_found
