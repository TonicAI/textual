import pytest
import uuid
from tonic_textual.classes.tonic_exception import DatasetNameAlreadyExists


def test_edit_dataset(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    name1 = str(uuid.uuid4())
    name2 = str(uuid.uuid4())
    dataset = textual.create_dataset(name1)

    dataset.edit(name=name2, label_allow_lists={"ORGANIZATION": ["that"]})

    assert dataset.name == name2


def test_edit_datasetname_to_conflict(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    name1 = str(uuid.uuid4())
    name2 = str(uuid.uuid4())
    textual.create_dataset(name1)
    dataset2 = textual.create_dataset(name2)

    with pytest.raises(DatasetNameAlreadyExists):
        dataset2.edit(name=name1)
