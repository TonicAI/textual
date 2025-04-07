import uuid
import re

from tests.utils.resource_utils import get_resource_path
from tests.utils.dataset_utils import poll_until_file_rescans


def test_upload_to_dataset(textual):
    dataset = textual.create_dataset(str(uuid.uuid4()))

    file_to_add = get_resource_path("simple_text_with_no_pii.txt")
    dataset.add_file(
        file_to_add,
        "simple_text_with_no_pii.txt",
    )
    def check_label_before(content):
        return "There is no pii here." == content
    
    poll_until_file_rescans(dataset, check_label_before)

    # There is no pii here.
    dataset.edit(
        label_allow_lists={"NAME_GIVEN": ["There"], "NAME_FAMILY": [" ([a-z]{2}) "]}
    )

    # Check for pattern "[NAME_GIVEN_*][NAME_FAMILY_*]no pii here." instead of specific suffixes
    def check_labels_after_allow_lists(content):
        pattern = (
            r"\[NAME_GIVEN_[A-Za-z0-9]+\]\[NAME_FAMILY_[A-Za-z0-9]+\]no pii here\."
        )
        return re.match(pattern, content) is not None

    poll_until_file_rescans(dataset, check_labels_after_allow_lists)

    dataset.edit(label_allow_lists={})
    poll_until_file_rescans(dataset, check_label_before)

    dataset.edit(
        label_allow_lists={"NAME_GIVEN": ["There"], "NAME_FAMILY": [" ([a-z]{2}) "]},
        label_block_lists={"NAME_GIVEN": ["There"]},
    )

    # Check for pattern "There[NAME_FAMILY_*]no pii here." instead of specific suffix
    def check_labels_after_block_lists(content):
        pattern = r"There\[NAME_FAMILY_[A-Za-z0-9]+\]no pii here\."
        return re.match(pattern, content) is not None

    poll_until_file_rescans(dataset, check_labels_after_block_lists)
