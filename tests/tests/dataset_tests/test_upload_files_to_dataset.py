import pytest
import uuid
import pymupdf

from tests.utils.resource_utils import get_resource_path
from tests.utils.dataset_utils import check_dataset_str


def test_upload_to_dataset(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    dataset = textual.create_dataset(str(uuid.uuid4()))

    dataset_file1 = dataset.add_file(
        get_resource_path("simple_file.txt"), "simple_file.txt"
    )
    dataset_file2 = dataset.add_file(
        get_resource_path("Sample Invoice.pdf"), "Invoice.pdf"
    )

    assert dataset_file1.name == "simple_file.txt"
    assert dataset_file2.name == "Invoice.pdf"

    # Will download file.  The file will be redacted/synthesized according to the dataset configuration.
    txt_file = list(filter(lambda x: x.name == "simple_file.txt", dataset.files))[0]
    txt_bytes = txt_file.download()
    redacted_text = txt_bytes.decode("utf-8").strip()

    # Get the original text from the file
    original_text = open(get_resource_path("simple_file.txt"), "r").read()

    # Check if redaction is working correctly
    check_dataset_str(original_text, redacted_text)
    pdf_file = list(filter(lambda x: x.name == "Invoice.pdf", dataset.files))[0]
    pdf_bytes = pdf_file.download()
    # Open with pymupdf and make sure there's no exceptions
    pdf_document = pymupdf.Document(stream=pdf_bytes)
    assert pdf_document.page_count > 0
    


def test_delete_file(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    dataset = textual.create_dataset(str(uuid.uuid4()))

    dataset.add_file(get_resource_path("simple_file.txt"), "simple_file.txt")

    assert len(dataset.files) == 1

    file_id = dataset.files[0].id
    dataset.delete_file(file_id)
    assert len(dataset.files) == 0


def test_add_file_to_dataset_argument_logic(textual):
    dataset = textual.create_dataset(str(uuid.uuid4()))

    # ensure that if both file path and file are provided we throw exceptoin
    with pytest.raises(Exception) as e_info:
        dataset.add_file(
            file_path=get_resource_path("simple_file.txt"),
            file=b"some bytes",
        )
        assert e_info.message == "You must only specify a file path or a file, not both"

    # ensure that if file is specified that we throw if name is not provided
    with pytest.raises(Exception) as e_info:
        dataset.add_file(file=b"some bytes")
        assert (
            e_info.message
            == "When passing in a file you must specify the file_name parameter as well"
        )

    # ensure that either file_path or file is specified
    with pytest.raises(Exception) as e_info:
        dataset.add_file()
        assert e_info.message == "Must specify either a file_path or file"
