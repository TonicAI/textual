import re
import time
import json
from typing import Tuple
from tonic_textual.redact_api import TonicTextual


def fetch_all_df_helper(setup_bill_gates_txt_dataset: Tuple[TonicTextual, str, str]):
    textual, dataset_name, dataset_path = setup_bill_gates_txt_dataset
    fetched_dataset = textual.get_dataset(dataset_name)
    original_text = open(dataset_path, "r").read()
    result_df = fetched_dataset.fetch_all_df()
    return result_df.iloc[0]["text"], original_text


def check_dataset_str(original_text: str, dataset_str: str):
    # Extract all redacted portions using regex pattern for [ENTITY_TYPE_*]
    redaction_pattern = r"\[(?:[A-Z]+(?:_[a-zA-Z0-9]+)*)\]"

    # Split by redaction pattern to get non-redacted segments
    non_redacted_segments = re.split(redaction_pattern, dataset_str)
    # Assert that there was at least one split performed
    assert len(non_redacted_segments) > 1, "No non-redacted segments found"

    # Check if the non-redacted portions exist in the original text
    for segment in non_redacted_segments:
        if segment.strip():  # Skip empty segments
            assert segment.strip() in original_text, (
                f"Non-redacted segment '{segment.strip()}' not found in original text"
            )


def poll_until_file_rescans(dataset, expected_content):
    num_download_attempts = 10
    attempts = 0

    while attempts < num_download_attempts:
        download_content = (
            dataset.files[0]
            .download(wait_between_retries=1, num_retries=100)
            .decode("utf-8")
            .strip()
        )
        if download_content == expected_content:
            break
        attempts = attempts + 1
        time.sleep(1)

    assert download_content == expected_content


def extract_json_strings(json_string):
    """
    Extract all strings from a nested JSON list structure.

    Args:
        json_string (str): A JSON string formatted as a potentially nested list structure.
        Example: '[["inner string 1", "inner string 2"], ["another string"]]'

    Returns:
        list: The extracted nested list structure with all strings.

    Raises:
        ValueError: If the JSON structure doesn't match the expected format or is invalid.
    """
    try:
        # Parse the JSON string
        parsed_json = json.loads(json_string)

        # Check if it's a list
        if not isinstance(parsed_json, list):
            raise ValueError("JSON structure is not a list")

        # Check that the list is a list of lists
        if not all(isinstance(item, list) for item in parsed_json):
            raise ValueError("JSON structure is not a list of lists")

        # Return the entire parsed structure
        return parsed_json

    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string")
