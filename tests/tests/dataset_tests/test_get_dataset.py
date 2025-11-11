import io
import uuid

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import PiiType
from tonic_textual.redact_api import TextualNer

import json
import pytest

from tests.utils.dataset_utils import (
    check_dataset_str,
    fetch_all_df_helper,
)

def test_get_all_datasets(textual: TextualNer):
    ds_name_one = str(uuid.uuid4()) + 'test-get-all-datasets-one'
    ds_one = textual.create_dataset(ds_name_one)
    ds_one.add_file(file_name = 'test-shelf.txt', file = create_file_stream("This is how I long my shelf: I do it with a long ruler."))

    ds_name_two = str(uuid.uuid4()) + 'test-get-all-datasets-two'
    ds_two = textual.create_dataset(ds_name_two)
    ds_two.add_file(file_name='test-gantry.txt', file=create_file_stream("Talking about how it's popping my bubbles; it's my gantry."))

    ds_all = textual.get_all_datasets()

    assert len(ds_all) >= 2, "list of all datasets contains less than two items"

    one_found = False
    two_found = False

    for ds in ds_all:
        if ds.name == ds_name_one:
            one_found = True
        if ds.name == ds_name_two:
            two_found = True

    assert one_found, "first dataset did not appear in list of all datasets"
    assert two_found, "second dataset did not appear in list of all datasets"

def test_get_dataset(textual: TextualNer):
    ds_name = str(uuid.uuid4()) + 'test-get-all-datasets-one'
    ds_out = textual.create_dataset(ds_name)
    ds_out.add_file(file_name = 'test-shelf.txt', file = create_file_stream("This is how I long my shelf: I do it with a long ruler."))

    person_age_metadata_out = PersonAgeGeneratorMetadata(
        scramble_unrecognized_dates=False,
        metadata=AgeShiftMetadata(age_shift_in_years=10)
    )

    ds_out.edit(
        generator_config={PiiType.LOCATION_COMPLETE_ADDRESS.name:PiiState.Redaction},
        generator_metadata={PiiType.PERSON_AGE:person_age_metadata_out}
    )

    ds_in = textual.get_dataset(ds_name)

    assert ds_in.generator_config[PiiType.LOCATION_COMPLETE_ADDRESS.name] == PiiState.Redaction
    assert ds_in.generator_metadata[PiiType.PERSON_AGE.name].metadata.age_shift_in_years == 10

def test_fetch_all_df(setup_bill_gates_txt_dataset):
    df_str, original_text = fetch_all_df_helper(setup_bill_gates_txt_dataset)
    check_dataset_str(original_text, df_str)


def test_fetch_all_df_without_pandas(monkeypatch, setup_bill_gates_txt_dataset):
    # Mocks pandas not being installed
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("No module named 'pandas'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)

    with pytest.raises(ImportError):
        fetch_all_df_helper(setup_bill_gates_txt_dataset)


def test_fetch_all_json(setup_bill_gates_txt_dataset):
    textual, dataset_name, dataset_path = setup_bill_gates_txt_dataset
    fetched_dataset = textual.get_dataset(dataset_name)
    json_dataset = fetched_dataset.fetch_all_json()
    # Convert the json which is a 2d list into a 2d list
    json_lst = json.loads(json_dataset)
    # Assert that it's 1 x 1 in size
    assert len(json_lst) == 1
    assert len(json_lst[0]) == 1
    check_dataset_str(open(dataset_path, "r").read(), json_lst[0][0])

def create_file_stream(txt: str) -> io.BytesIO:
    return io.BytesIO(txt.encode('utf-8'))
