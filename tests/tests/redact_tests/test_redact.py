import json
import pytest
from tonic_textual.enums.pii_state import PiiState
from tests.utils.redact_utils import (
    check_redaction,
)
from redaction_data import (
    DICT_SAMPLE,
    NAMES_TEXT,
    XML_SAMPLE,
    HTML_SAMPLE,
)


# Standard synthesis config for tests
TYPES_TO_REDACT = {
    "ORGANIZATION",
    "NAME_GIVEN",
    "NAME_FAMILY",
    "LOCATION_ADDRESS",
    "LOCATION_CITY",
    "LOCATION_STATE",
    "LOCATION_ZIP",
    "NUMERIC_VALUE",
    "DATE_TIME",
    "MONEY",
}
SEEDS = [None, 1234, 2345]


def test_json_redaction_basics(textual):
    """Test basic JSON redaction functionality."""
    original_json = json.dumps(DICT_SAMPLE)

    # Redact with just zip synthesis
    redaction = textual.redact_json(original_json, {"LOCATION_ZIP": "Synthesis"})

    # Ensure we got spans back
    assert len(redaction.de_identify_results) > 0, "No spans were returned"

    # Validate valid JSON
    try:
        json_data = json.loads(redaction.redacted_text)
        assert isinstance(json_data, dict), "Redacted text is not a valid JSON object"
    except json.JSONDecodeError:
        pytest.fail("Redacted text is not valid JSON")

    # Check what was synthesized vs redacted
    assert isinstance(json_data["address"]["zip"], int), (
        "ZIP should still be an integer"
    )
    assert json_data["address"]["zip"] != 1234, "ZIP should be modified"

    # Check for redaction patterns in person fields
    assert any(
        isinstance(json_data["person"][key], str)
        and json_data["person"][key].startswith("[")
        for key in ["first", "last"]
    ), "Expected redaction patterns in person fields"


def test_json_redaction_with_seed(textual):
    """Test JSON redaction with seed is deterministic."""
    original_json = json.dumps(DICT_SAMPLE)

    # Local function to run redaction with seed
    def run_redaction_with_seed(seed_value):
        return textual.redact_json(
            original_json, {"LOCATION_ZIP": "Synthesis"}, random_seed=seed_value
        )

    # Run twice with same seed value
    seed_value = 5
    redaction1 = run_redaction_with_seed(seed_value)
    redaction2 = run_redaction_with_seed(seed_value)

    # Verify same result
    assert redaction1.redacted_text == redaction2.redacted_text, (
        "Same seed should produce same output"
    )

    # Validate JSON
    try:
        json_data = json.loads(redaction1.redacted_text)
    except json.JSONDecodeError:
        pytest.fail("Redacted text is not valid JSON")

    # ZIP should be synthesized, not redacted
    assert isinstance(json_data["address"]["zip"], int)
    assert json_data["address"]["zip"] != 1234


def test_json_redaction_with_allow_lists(textual):
    """Test JSON redaction with jsonpath allow lists."""
    original_json = json.dumps(DICT_SAMPLE)

    # Create redaction with allow lists
    redaction = textual.redact_json(
        original_json,
        generator_config={
            "DATE_TIME": "Synthesis",
            "LOCATION_ZIP": "Synthesis",
            "HEALTHCARE_ID": "Synthesis",
        },
        jsonpath_allow_lists={
            "PHONE_NUMBER": ["$.person.first"],
            "DATE_TIME": ["$.person.last"],
            "HEALTHCARE_ID": ["$.address.city"],
            "ORGANIZATION": [
                "$.address.state",
                "$.address.street",
            ],
        },
        random_seed=5,
    )

    # Validate JSON
    try:
        json_data = json.loads(redaction.redacted_text)
    except json.JSONDecodeError:
        pytest.fail("Redacted text is not valid JSON")

    # Check that allow-list worked for different entity types
    assert json_data["person"]["first"].startswith("[PHONE_NUMBER_"), (
        "First name should be treated as phone number"
    )

    assert isinstance(json_data["person"]["last"], str)
    assert not json_data["person"]["last"].startswith("["), (
        "Last name should be synthesized as date time, not redacted"
    )

    assert json_data["address"]["state"].startswith("[ORGANIZATION_"), (
        "Address state should be treated as organization"
    )

    assert isinstance(json_data["address"]["city"], str)
    assert not json_data["address"]["city"].startswith("["), (
        "Address city should be synthesized as healthcare ID, not redacted"
    )


def test_generator_defaults_off(textual):
    """Test that generator_default=Off keeps most entities intact."""
    response = textual.redact(
        NAMES_TEXT,
        generator_default=PiiState.Off,
        generator_config={"NAME_GIVEN": PiiState.Redaction},
    )

    # Use check_redaction utility to validate results
    check_redaction(
        NAMES_TEXT,
        response.redacted_text,
        spans=response.de_identify_results,
        generator_default=PiiState.Off,
        generator_config={"NAME_GIVEN": PiiState.Redaction},
        expected_items=[
            ("Luke", PiiState.Redaction),
            ("McFee", PiiState.Off),
            ("Japan", PiiState.Off),
        ],
    )


def test_surrogate_pairs(textual):
    """Test handling of emoji and special characters in redaction."""
    # Text with emojis and special characters
    text = "Come down to @safehouse tonight and check us out!! We got some 🤤mouthwatering🤤 TACOS.🌮, BURRITOS🌯, and QUESADILLAS🧀"

    # Simply test that it doesn't crash when processing text with emojis and surrogate pairs
    try:
        response = textual.redact(text)
        assert response.redacted_text is not None, "Redacted text should not be None"
        assert len(response.redacted_text) > 0, "Redacted text should not be empty"
        assert response.redacted_text.startswith("Come down to"), (
            "Start of text should be preserved"
        )

        # Check emoji preservation
        assert "🤤" in response.redacted_text, "Expected emoji to be preserved"
        assert "🌮" in response.redacted_text, "Expected emoji to be preserved"
    except Exception as e:
        pytest.fail(f"Failed to properly handle surrogate pairs in text: {e}")


def test_pci_synthesis(textual):
    """Test credit card PCI data synthesis."""
    text = "My credit card is 5555-5555-1111-2223, cvv is eight five two, and expiration is nine twenty five"

    response = textual.redact(text, generator_default="Synthesis")

    # Use check_redaction for comprehensive validation
    check_redaction(
        text,
        response.redacted_text,
        spans=response.de_identify_results,
        generator_default=PiiState.Synthesis,
        expected_items=[("5555-5555-1111-2223", PiiState.Synthesis)],
    )


@pytest.mark.parametrize("xml_string", XML_SAMPLE)
def test_xml_redaction(textual, xml_string):
    """Test XML redaction with different XML samples."""
    response = textual.redact_xml(xml_string)

    # Check that XML is well-formed
    assert response.redacted_text.startswith("<"), "Redacted XML should start with <"

    # Check that we have spans
    assert len(response.de_identify_results) > 0, "Expected spans in result"

    # Check names are redacted
    check_redaction(
        xml_string,
        response.redacted_text,
        spans=response.de_identify_results,
        expected_items=[
            ("John", PiiState.Redaction),
            ("Jim", PiiState.Redaction),
            ("Doe", PiiState.Redaction),
        ],
    )

    # If complex XML, do more checks
    if len(xml_string) > 100:
        assert response.redacted_text.startswith("<?xml"), (
            "Redacted XML should start with <?xml"
        )
        assert response.redacted_text.endswith("</PersonInfo>"), (
            "Redacted XML should end with </PersonInfo>"
        )

        check_redaction(
            xml_string,
            response.redacted_text,
            spans=response.de_identify_results,
            expected_items=[
                ("john.doe@example.com", PiiState.Redaction),
                ("555-6789", PiiState.Redaction),
                ("187-65-4321", PiiState.Redaction),
            ],
        )

        # Check different entity types (at least 3)
        entity_types = {span["label"] for span in response.de_identify_results}
        assert len(entity_types) >= 3, "Expected at least 3 different entity types"

    # Check xml_path is present in spans
    for span in response.de_identify_results:
        assert "xml_path" in span, "Expected xml_path in span"


def test_html_redaction(textual):
    """Test HTML redaction with selective entity types."""
    # Set some entity types to Off
    response = textual.redact_html(
        HTML_SAMPLE, {"PHONE_NUMBER": "Off", "EMAIL_ADDRESS": "Off", "URL": "Off"}
    )

    # Check HTML structure preserved
    assert response.redacted_text.startswith("<html>"), (
        "Redacted HTML should start with <html>"
    )
    assert response.redacted_text.endswith("</html>"), (
        "Redacted HTML should end with </html>"
    )

    # Use check_redaction for comprehensive validation
    check_redaction(
        HTML_SAMPLE,
        response.redacted_text,
        spans=response.de_identify_results,
        generator_config={
            "PHONE_NUMBER": PiiState.Off,
            "EMAIL_ADDRESS": PiiState.Off,
            "URL": PiiState.Off,
        },
        expected_items=[
            ("John", PiiState.Redaction),
            ("Doe", PiiState.Redaction),
            ("22", PiiState.Redaction),
            ("johndoe@example.com", PiiState.Off),
            ("(123) 456-7890", PiiState.Off),
        ],
    )
