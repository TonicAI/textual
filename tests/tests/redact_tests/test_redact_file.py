import re
import pytest
import fitz
from tonic_textual.enums.pii_state import PiiState
from tests.utils.redact_utils import (
    check_redaction,
    create_custom_entity,
    delete_custom_entity,
    perform_file_redaction,
)
from tests.utils.resource_utils import (
    read_resource_file,
    get_resource_path,
)


@pytest.mark.parametrize(
    "filename",
    ["simple_file.txt", "simple_file.csv"],
)
@pytest.mark.parametrize(
    "generator_default", [PiiState.Off, PiiState.Redaction, PiiState.Synthesis]
)
@pytest.mark.parametrize(
    "generator_config",
    [
        None,
        {"NAME_GIVEN": PiiState.Synthesis, "LOCATION_CITY": PiiState.Synthesis},
        {"NAME_GIVEN": PiiState.Redaction, "LOCATION_CITY": PiiState.Redaction},
        {"NAME_GIVEN": PiiState.Off, "LOCATION_CITY": PiiState.Off},
        {"NAME_GIVEN": PiiState.Synthesis, "LOCATION_CITY": PiiState.Redaction},
    ],
)
def test_redact_file(textual, filename, generator_default, generator_config):
    original_content, output = perform_file_redaction(
        textual,
        filename,
        generator_default=generator_default,
        generator_config=generator_config,
    )
    check_redaction(
        original_content,
        output,
        generator_default=generator_default,
        generator_config=generator_config if generator_config else {},
    )


@pytest.mark.parametrize("filename", ["emoji_file.txt", "emoji_file.csv"])
@pytest.mark.parametrize(
    "generator_default", [PiiState.Off, PiiState.Redaction, PiiState.Synthesis]
)
def test_redact_file_with_emoji(textual, filename, generator_default):
    original_content, output = perform_file_redaction(
        textual,
        filename,
        generator_default=generator_default,
    )

    check_redaction(
        original_content,
        output,
        generator_default=generator_default,
        generator_config={},
    )

    # Check that the emoji is preserved
    assert "🌮" in output, "Expected taco emoji to be preserved"
    assert "🙏" in output, "Expected prayer emoji to be preserved"

@pytest.mark.parametrize(
    "redaction_type", [PiiState.Redaction, PiiState.Synthesis, PiiState.Off]
)
def test_redact_file_with_custom_entity(textual, redaction_type):
    custom_entity = create_custom_entity(textual, ["name"])
    custom_entity_name = custom_entity["name"]

    # Perform redaction
    original_content, output = perform_file_redaction(
        textual,
        "simple_file.txt",
        generator_config={custom_entity_name: redaction_type},
        generator_default=PiiState.Off,
        custom_entities=[custom_entity_name],
    )
    
    delete_custom_entity(textual, custom_entity_name)

    # Skip the check_redaction for custom entities - it has special handling needs
    # Just verify the output text patterns directly

    pattern = r"my (.+) is adam kamor\. I live in atlanta\."
    match = re.match(pattern, output.strip(), re.IGNORECASE)

    # Ensure we got a match
    assert match is not None, f"Regex pattern didn't match output: {output}"

    name_result = match.group(1).lower()

    if redaction_type == PiiState.Redaction:
        # For redaction, check for token pattern
        assert "[" in name_result and "]" in name_result, "Expected redaction pattern"
    elif redaction_type == PiiState.Synthesis:
        # For synthesis, just check that the name changed
        assert name_result != "name", "Expected synthesized name"
    else:
        # For Off mode, name should be preserved
        assert name_result == "name", "Expected original text"


def test_redact_file_same_seed(textual):
    """
    Test that redaction with the same seed produces the same results.
    This verifies deterministic behavior when using a specific random seed.
    """

    # Local function to run redaction with a specific seed
    def run_redaction_with_seed(seed_value):
        return perform_file_redaction(
            textual,
            "simple_file.txt",
            generator_default=PiiState.Redaction,
            random_seed=seed_value,
        )

    # Run twice with the same seed
    seed_value = 12345
    original_content1, output1 = run_redaction_with_seed(seed_value)
    original_content2, output2 = run_redaction_with_seed(seed_value)

    # Verify the original content is the same in both runs
    assert original_content1 == original_content2, (
        "Original content should be identical"
    )

    # Verify that outputs are identical when using the same seed
    assert output1 == output2, "Outputs should be identical when using the same seed"

    # Run again with a different seed to confirm it produces different results
    _, output_different_seed = perform_file_redaction(
        textual,
        "simple_file.txt",
        generator_default=PiiState.Redaction,
        random_seed=67890,
    )

    # Outputs should be different with a different seed
    assert output1 != output_different_seed, (
        "Outputs should differ with different seeds"
    )


@pytest.mark.parametrize(
    "generator_default", [PiiState.Redaction, PiiState.Synthesis, PiiState.Off]
)
def test_consistency_between_redact_methods(textual, generator_default):
    resource_file = read_resource_file("simple_file.txt")
    seed = 12345

    _, file_output = perform_file_redaction(
        textual,
        "simple_file.txt",
        generator_default=generator_default,
        random_seed=seed,
    )
    file_output = file_output.strip()

    redact_output = textual.redact(
        resource_file,
        generator_default=generator_default,
        random_seed=seed,
    ).redacted_text.strip()

    assert file_output == redact_output, (
        "Expected same output from file and direct redaction"
    )


@pytest.mark.parametrize(
    "generator_default", [PiiState.Redaction, PiiState.Synthesis, PiiState.Off]
)
def test_redact_file_pdf(textual, generator_default):
    """Test PDF redaction preserves structure while redacting content."""
    # Perform redaction on PDF file
    _, output_bytes = perform_file_redaction(
        textual,
        "Robin_Hood.pdf",
        generator_default=generator_default,
    )

    # Get the original PDF content
    with open(get_resource_path("Robin_Hood.pdf"), "rb") as f:
        original_pdf_bytes = f.read()

    # Extract text from original PDF
    original_doc = fitz.open("pdf", original_pdf_bytes)
    original_page = original_doc.load_page(0)
    original_text = original_page.get_text()

    # Extract text from redacted PDF
    output_doc = fitz.open("pdf", output_bytes)
    output_page = output_doc.load_page(0)
    output_text = output_page.get_text()

    # For PDF files, do a more basic check
    if generator_default != PiiState.Off:
        # Verify text was modified when not in Off mode
        assert original_text != output_text, (
            "Text should be modified with redaction or synthesis"
        )
    else:
        assert original_text == output_text, "Text should be preserved in Off mode"
    assert len(output_text) > 0, "Expected PDF to have content after redaction"
