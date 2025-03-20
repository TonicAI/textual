import pytest

from tests.utils.dataset_utils import (
    check_dataset_str,
    fetch_all_df_helper,
)


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
    check_dataset_str(open(dataset_path, "r").read(), json_dataset)
