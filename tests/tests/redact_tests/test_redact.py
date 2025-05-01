import json
import pytest
from tonic_textual.enums.pii_state import PiiState
from tests.utils.redact_utils import (
    check_redaction,
)
from tests.tests.redact_tests.redaction_data import (
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
    assert json_data["address"]["zip"] != DICT_SAMPLE["address"]["zip"], "ZIP should be modified"

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
    assert json_data["address"]["zip"] != DICT_SAMPLE["address"]["zip"]


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

    # Prepare expected items based on which XML sample we're testing
    if "Jim Doe" in xml_string:
        expected_items = [
            ("Jim", PiiState.Redaction),
            ("Doe", PiiState.Redaction),
        ]
    else:  # Complex XML with John Doe
        expected_items = [
            ("John", PiiState.Redaction),
            ("Doe", PiiState.Redaction),
        ]

    # For XML tests, only check that expected entities are redacted
    # and skip the reconstruction check which can be problematic for XML
    for entity, state in expected_items:
        if state == PiiState.Off:
            assert entity in response.redacted_text, (
                f"Expected {entity} to be in redacted text"
            )
        else:
            assert entity not in response.redacted_text, (
                f"Expected {entity} to be redacted"
            )

    # Verify that XML is valid by checking basic structure
    assert response.redacted_text.strip().startswith("<"), (
        "Redacted text should start with <"
    )
    assert response.redacted_text.strip().endswith(">"), (
        "Redacted text should end with >"
    )

    # If complex XML, do more checks
    if len(xml_string) > 100:
        assert response.redacted_text.startswith("<?xml"), (
            "Redacted XML should start with <?xml"
        )
        assert response.redacted_text.endswith("</PersonInfo>"), (
            "Redacted XML should end with </PersonInfo>"
        )

        additional_expected_items = [
            ("john.doe@example.com", PiiState.Redaction),
            ("555-6789", PiiState.Redaction),
            ("187-65-4321", PiiState.Redaction),
        ]

        # Check additional items are redacted
        for item, state in additional_expected_items:
            if state == PiiState.Off:
                assert item in response.redacted_text, (
                    f"Expected {item} to be in redacted text"
                )
            else:
                assert item not in response.redacted_text, (
                    f"Expected {item} to be redacted"
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


def test_llm_synthesis_basic(textual):
    """Test basic LLM synthesis functionality."""
    sample_text = "My name is John, and today I am demoing Textual, a software product created by Tonic"

    # Run LLM synthesis
    response = textual.llm_synthesis(sample_text)

    # Check that response contains the expected fields
    assert response.original_text == sample_text, "Original text should match input"
    assert response.redacted_text != sample_text, (
        "Redacted text should be different from original"
    )
    assert len(response.de_identify_results) > 0, "Should have detected entities"
    assert response.usage is not None, "Should have usage information"

    # Verify at least NAME_GIVEN and ORGANIZATION are detected
    detected_labels = {result.label for result in response.de_identify_results}
    assert "NAME_GIVEN" in detected_labels, "Expected NAME_GIVEN to be detected"
    assert "ORGANIZATION" in detected_labels, "Expected ORGANIZATION to be detected"

    # Check that known tokens aren't present (confirming it's not just tokenization)
    assert "[NAME_GIVEN_" not in response.redacted_text, (
        "Should not contain tokenization patterns"
    )
    assert "[ORGANIZATION_" not in response.redacted_text, (
        "Should not contain tokenization patterns"
    )


def test_llm_synthesis_with_config(textual):
    """Test LLM synthesis with handling configuration."""
    sample_text = "My name is John, and today I am demoing Textual, a software product created by Tonic"

    # Configure to only synthesize organization and leave other entities as-is
    generator_config = {"ORGANIZATION": PiiState.Synthesis}
    generator_default = PiiState.Off

    response = textual.llm_synthesis(
        sample_text,
        generator_config=generator_config,
        generator_default=generator_default,
    )

    # John should still be present (default is Off)
    assert "John" in response.redacted_text, "NAME_GIVEN should not be altered"

    # Tonic should be replaced (explicitly set to Synthesis)
    assert "Tonic" not in response.redacted_text, "ORGANIZATION should be synthesized"

    # Check that the replacement appears natural (not tokenized)
    for result in response.de_identify_results:
        if result.label == "ORGANIZATION":
            assert result.text == "Tonic", "Expected original text to be Tonic"
            # The new text should be in the redacted output but not pattern-like [ORG_xyz]
            assert "[" not in response.redacted_text, (
                "Redacted text should not contain token patterns"
            )

def test_llm_synthesis_with_block_lists(textual):
    """Test LLM synthesis with label block lists."""
    sample_text = "My name is John and I live in Atlanta with my friend Alice"

    # Block lists configuration - block 'John' from being treated as NAME_GIVEN
    label_block_lists = {"NAME_GIVEN": ["John"]}

    response = textual.llm_synthesis(
        sample_text,
        label_block_lists=label_block_lists,
        generator_default=PiiState.Synthesis,
    )

    # Verify "John" is preserved (blocked from detection)
    assert "John" in response.redacted_text, (
        "NAME_GIVEN in block list should be preserved"
    )

    # But other names (Alice) should be synthesized
    assert "Alice" not in response.redacted_text, "Other names should be synthesized"

    # Check Atlanta is synthesized (not in block list)
    assert "Atlanta" not in response.redacted_text, (
        "LOCATION_CITY should be synthesized"
    )


def test_llm_synthesis_with_allow_lists(textual):
    """Test LLM synthesis with label allow lists."""
    sample_text = "My pet name is Rex and I live in Dogtown"

    # Allow list configuration - treat 'Rex' as NAME_GIVEN and 'Dogtown' as LOCATION_CITY
    label_allow_lists = {"NAME_GIVEN": ["Rex"], "LOCATION_CITY": ["Dogtown"]}

    response = textual.llm_synthesis(
        sample_text,
        label_allow_lists=label_allow_lists,
        generator_default=PiiState.Synthesis,
    )

    # Verify "Rex" is not in result (allowed to be treated as NAME_GIVEN)
    assert "Rex" not in response.redacted_text, (
        "Allowed NAME_GIVEN should be synthesized"
    )

    # Verify "Dogtown" is not in result (allowed to be treated as LOCATION_CITY)
    assert "Dogtown" not in response.redacted_text, (
        "Allowed LOCATION_CITY should be synthesized"
    )

    # Check detected entities include our allow-listed items
    detected_labels_with_text = [
        (result.label, result.text) for result in response.de_identify_results
    ]
    assert ("NAME_GIVEN", "Rex") in detected_labels_with_text, (
        "Rex should be detected as NAME_GIVEN"
    )
    assert ("LOCATION_CITY", "Dogtown") in detected_labels_with_text, (
        "Dogtown should be detected as LOCATION_CITY"
    )


def test_llm_synthesis_comparison_with_redact(textual):
    """Test that llm_synthesis produces different output compared to regular redact with synthesis."""
    sample_text = (
        "My name is John Smith, and I work for Acme Corporation in Seattle, WA."
    )

    # Use the same configuration for both methods
    generator_config = {
        "NAME_GIVEN": PiiState.Synthesis,
        "NAME_FAMILY": PiiState.Synthesis,
        "ORGANIZATION": PiiState.Synthesis,
        "LOCATION_CITY": PiiState.Synthesis,
    }

    # Fix seed for deterministic comparison
    random_seed = 12345

    # Get results from both methods
    llm_response = textual.llm_synthesis(
        sample_text, generator_config=generator_config, random_seed=random_seed
    )

    regular_response = textual.redact(
        sample_text, generator_config=generator_config, random_seed=random_seed
    )

    # They should both detect the same entities
    llm_entities = {(r.label, r.text) for r in llm_response.de_identify_results}
    regular_entities = {(r.label, r.text) for r in regular_response.de_identify_results}
    assert llm_entities == regular_entities, (
        "Both methods should detect the same entities"
    )

    # But the synthesized output should be different
    assert llm_response.redacted_text != regular_response.redacted_text, (
        "LLM synthesis should produce different output than regular synthesis"
    )

    # LLM output should not contain tokenization patterns
    assert "[" not in llm_response.redacted_text, (
        "LLM synthesis should not use tokenization"
    )

    # Regular output with synthesis might still use tokenization patterns in some cases
    # but this is implementation-dependent, so we don't assert on it


def test_llm_synthesis_error_handling(textual):
    """Test error handling in llm_synthesis with invalid parameters."""
    sample_text = "My name is John Smith."

    # Test with invalid generator_default value
    with pytest.raises(Exception) as excinfo:
        textual.llm_synthesis(sample_text, generator_default="Invalid")
    assert "Invalid option for generator_default" in str(excinfo.value)

    # Test with invalid generator_config value
    with pytest.raises(Exception) as excinfo:
        textual.llm_synthesis(sample_text, generator_config={"NAME_GIVEN": "Invalid"})
    assert "Invalid configuration for generator_config" in str(excinfo.value)

    # Test with empty text
    empty_response = textual.llm_synthesis("")
    assert empty_response.original_text == "", "Original text should be empty"
    assert len(empty_response.de_identify_results) == 0, (
        "No entities should be detected in empty text"
    )
