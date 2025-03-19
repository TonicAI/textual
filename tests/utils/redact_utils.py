from typing import (
    List,
    Dict,
    Optional,
    Set,
    Union,
    Pattern,
)
import uuid
from requests import RequestException
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.enums.pii_state import PiiState
import re
import os
from tonic_textual.redact_api import TonicTextual

from tests.utils.resource_utils import get_resource_path


def create_custom_entity(textual: TonicTextual, regexes: List[str]):
    try:
        name = str(uuid.uuid4()).replace("-", " ")[:50]
        payload = {
            "datasetIds": [],
            "pipelineIds": [],
            "entries": {"regexes": regexes},
            "displayName": name,
            "enabledAutomatically": False,
            "startLightRescan": False,
        }
        p = textual.client.http_post("/api/custom_pii_entities", data=payload)
        return p
    except RequestException as req_err:
        raise req_err


def perform_file_redaction(
    textual: TonicTextual,
    filename: str,
    generator_config: Optional[Dict[str, PiiState]] = None,
    generator_default: PiiState = PiiState.Redaction,
    random_seed: Optional[int] = None,
    custom_entities: Optional[List[str]] = None,
    wait_between_retries: int = 1,
    num_retries: int = 120,
):
    """
    Perform file redaction with common parameters.

    Args:
        textual: Textual client instance
        filename: Name of the file in resources directory to redact
        generator_config: Optional configuration for redaction (default: None)
        random_seed: Optional random seed (default: None)
        custom_entities: Optional list of custom entities (default: None)
        wait_between_retries: Wait time between retries (default: 1)
        num_retries: Number of retries (default: 120)

    Returns:
        Tuple of (original_content, redacted_output) where both are strings
    """
    file_path = get_resource_path(filename)
    binary_extensions = [".pdf", ".xlsx", ".docx"]
    mode = "rb" if os.path.splitext(filename)[1] in binary_extensions else "r"
    encoding = "utf-8" if mode == "r" else None

    with open(file_path, mode, encoding=encoding) as f:
        if mode == "r":
            original_content = f.read()
            f.seek(0)
        else:
            original_content = None  # Binary content

        job = textual.start_file_redaction(f, filename, custom_entities=custom_entities)

    output = textual.download_redacted_file(
        job,
        generator_config=generator_config,
        generator_default=generator_default,
        random_seed=random_seed,
        wait_between_retries=wait_between_retries,
        num_retries=num_retries,
    )

    if mode == "r":
        output = output.decode("utf-8")

    return original_content, output


def validate_spans(text: str, spans: List[Replacement]) -> bool:
    """
    Validate that the spans detected by the redact function are valid.
    This checks:
    1. Each span's text matches the text at the specified start/end indices
    2. Spans don't overlap
    3. Start/end indices are within text bounds

    Args:
        text: The original text
        spans: List of spans returned by redact function

    Returns:
        True if all spans are valid, otherwise False
    """
    # Sort spans by start position
    sorted_spans = sorted(spans, key=lambda span: span["start"])

    # Check text bounds and that spans don't overlap
    prev_end = -1
    for span in sorted_spans:
        start = span["start"]
        end = span["end"]

        # Check indices are within bounds
        if start < 0 or end > len(text):
            return False

        # Check span text matches text at indices
        span_text = text[start:end]
        if span["text"] != span_text:
            return False

        # Check spans don't overlap (can be adjacent but not overlapping)
        if start < prev_end:
            return False

        prev_end = end

    return True


def reconstruct_original_text(redacted_text: str, spans: List[Replacement]) -> str:
    """
    Attempt to reconstruct the original text from redacted text and spans.
    This is a way to verify redaction without depending on exact output format.

    Args:
        redacted_text: The redacted text
        spans: List of spans returned by redact function

    Returns:
        The reconstructed original text
    """
    # Create a copy of the redacted text
    result = redacted_text

    # Sort spans in reverse order by new_start to avoid index issues when replacing
    sorted_spans = sorted(spans, key=lambda span: span["new_start"], reverse=True)

    # Replace each redacted span with its original text
    for span in sorted_spans:
        if "new_start" in span and "new_end" in span and "text" in span:
            result = (
                result[: span["new_start"]] + span["text"] + result[span["new_end"] :]
            )

    return result


def verify_redacted_text_format(
    redacted_text: str, pii_states_used: Set[PiiState]
) -> bool:
    """
    Verify that the redacted text follows expected format patterns.
    This checks that redacted sections match expected patterns based on redaction type.

    Args:
        redacted_text: The redacted text
        pii_states_used: The set of PiiStates used in the redaction

    Returns:
        True if format is valid, otherwise False
    """
    # If the set only contains only Synthesis, then return True
    if len(pii_states_used) == 1 and PiiState.Synthesis in pii_states_used:
        return True

    pattern = r"\[(\w+)_[a-zA-Z0-9]{1,10}\]"
    matches = re.findall(pattern, redacted_text)

    if PiiState.Redaction in pii_states_used:
        return len(matches) > 0
    else:
        return len(matches) == 0


def check_redaction(
    original_text: str,
    redacted_text: str,
    spans: List[Replacement] = [],
    generator_default: PiiState = PiiState.Redaction,
    generator_config: Dict[str, PiiState] = {},
    expected_items: List[Dict[Union[str, Pattern], PiiState]] = [],
):
    """
    Comprehensive validation of redaction results combining the functionality of
    assert_redaction, verify_redacted_text_format, and validate_redaction_result.

    Args:
        original_text: The original text before redaction
        redaction_response: A RedactionResponse object returned from the redaction API
        spans: List of spans returned by redact function
        generator_default: The default redaction type the API was configured with
        generator_config: The generator config the API was configured with
        expected_items: Expected items to either be present or not present in the redacted text.
            The key is the regex or literal string and value is how it should be redacted.
            How it should be redacted determines if it should be present or not present in the redacted text.

    Returns:
        True if all validation checks pass, raises AssertionError otherwise
    """

    pii_states_used = set([result.pii_state for result in spans])
    pii_states_used.add(generator_default)
    pii_states_used.update(generator_config.values())

    # 1. Check text was modified
    if PiiState.Redaction in pii_states_used or PiiState.Synthesis in pii_states_used:
        assert original_text != redacted_text, "Text should be modified"

    # 2. Verify redacted text format
    assert verify_redacted_text_format(redacted_text, pii_states_used), (
        f"Redacted text format doesn't match expected pattern for {pii_states_used}"
    )

    # 3. Check that the expected entity results are present. If the PiiState is Off, then the entity should be present. Else, it should not be present.
    for entity, expected_result in expected_items:
        if isinstance(entity, Pattern):
            # For regex patterns
            if expected_result == PiiState.Off:
                assert re.search(entity, redacted_text), (
                    f"Expected pattern {entity.pattern} not found in redacted text"
                )
            else:
                assert not re.search(entity, redacted_text), (
                    f"Expected pattern {entity.pattern} to be redacted"
                )
        else:
            # For string literals
            if expected_result == PiiState.Off:
                assert entity in redacted_text, (
                    f"Expected entity {entity} not found in redacted text"
                )
            else:
                assert entity not in redacted_text, (
                    f"Expected entity {entity} to be redacted"
                )

    if len(spans) == 0:
        return

    # 4. Validate spans
    assert validate_spans(original_text, spans), (
        "Spans are invalid for the original text"
    )

    # 5. Test that reconstruction works
    reconstructed = reconstruct_original_text(redacted_text, spans)
    assert reconstructed.strip() == original_text.strip(), (
        "Reconstructed text does not match original"
    )
