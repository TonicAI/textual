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
    redaction = textual.redact_json(original_json, "Redaction", {"LOCATION_ZIP": PiiState.Synthesis})

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
            original_json, "Redaction", {"LOCATION_ZIP": PiiState.Synthesis}, random_seed=seed_value
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
            "DATE_TIME": PiiState.Synthesis,
            "LOCATION_ZIP": PiiState.Synthesis,
            "HEALTHCARE_ID": PiiState.Synthesis,
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
def test_generator_config_strings(textual):
    response_string_redact = textual.redact(
        NAMES_TEXT,
        generator_default='Off',
        generator_config={"NAME_GIVEN": 'Redaction'},
    )
    response_enum_redact = textual.redact(
        NAMES_TEXT,
        generator_default=PiiState.Off,
        generator_config={"NAME_GIVEN": PiiState.Redaction},
    )
    # Check that the redacted text strings are the same
    assert response_string_redact.redacted_text == response_enum_redact.redacted_text

    response_string_synthesis = textual.redact(
        NAMES_TEXT,
        generator_default='Off',
        generator_config={"NAME_GIVEN": 'Synthesis'},
    )
    response_enum_synthesis = textual.redact(
        NAMES_TEXT,
        generator_default=PiiState.Off,
        generator_config={"NAME_GIVEN": PiiState.Synthesis},
    )
    # Check that the redacted text strings are the same
    assert response_string_synthesis.redacted_text == response_enum_synthesis.redacted_text


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

    response = textual.redact(text, generator_default=PiiState.Synthesis)

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
        HTML_SAMPLE, "Redaction", {"PHONE_NUMBER": PiiState.Off, "EMAIL_ADDRESS": PiiState.Off, "URL": PiiState.Off}
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


@pytest.mark.parametrize("synthesis_state", [PiiState.GroupingSynthesis, PiiState.ReplacementSynthesis])
def test_synthesis_basic(textual, synthesis_state):
    """Test basic synthesis functionality."""
    sample_text = "My name is John, and today I am demoing Textual, a software product created by Tonic"

    # Run synthesis
    response = textual.redact(sample_text, generator_default=synthesis_state)

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


@pytest.mark.parametrize("synthesis_state", [PiiState.GroupingSynthesis, PiiState.ReplacementSynthesis])
def test_synthesis_with_config(textual, synthesis_state):
    """Test synthesis with handling configuration."""
    sample_text = "My name is John, and today I am demoing Textual, a software product created by Tonic"

    # Configure to only synthesize organization and leave other entities as-is
    generator_config = {"ORGANIZATION": synthesis_state}
    generator_default = PiiState.Off

    response = textual.redact(
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

@pytest.mark.parametrize("synthesis_state", [PiiState.GroupingSynthesis, PiiState.ReplacementSynthesis])
def test_synthesis_with_block_lists(textual, synthesis_state):
    """Test synthesis with label block lists."""
    sample_text = "My name is John and I live in Atlanta with my friend Alice"

    # Block lists configuration - block 'John' from being treated as NAME_GIVEN
    label_block_lists = {"NAME_GIVEN": ["John"]}

    response = textual.redact(
        sample_text,
        label_block_lists=label_block_lists,
        generator_default=synthesis_state,
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


@pytest.mark.parametrize("synthesis_state", [PiiState.GroupingSynthesis, PiiState.ReplacementSynthesis])
def test_synthesis_with_allow_lists(textual, synthesis_state):
    """Test synthesis with label allow lists."""
    sample_text = "My pet name is Rex and I live in Dogtown"

    # Allow list configuration - treat 'Rex' as NAME_GIVEN and 'Dogtown' as LOCATION_CITY
    label_allow_lists = {"NAME_GIVEN": ["Rex"], "LOCATION_CITY": ["Dogtown"]}

    response = textual.redact(
        sample_text,
        label_allow_lists=label_allow_lists,
        generator_default=synthesis_state,
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


def test_all_pii_states_mixed(textual):
    """Test using all PII states (Off, Redaction, Synthesis, GroupingSynthesis, ReplacementSynthesis) in one call."""
    sample_text = (
        "John Smith works at Acme Corporation in Seattle, WA 98101. "
        "His email is john.smith@acme.com and his phone is 555-123-4567. "
        "He was born on January 15, 1990."
    )

    # Use all different PII states
    generator_config = {
        "NAME_GIVEN": PiiState.Off,  # Keep as-is
        "NAME_FAMILY": PiiState.Redaction,  # Tokenize
        "ORGANIZATION": PiiState.Synthesis,  # Standard synthesis
        "LOCATION_CITY": PiiState.GroupingSynthesis,  # LLM grouping synthesis
        "LOCATION_STATE": PiiState.ReplacementSynthesis,  # LLM replacement synthesis
        "LOCATION_ZIP": PiiState.Redaction,  # Tokenize
        "EMAIL_ADDRESS": PiiState.Synthesis,  # Standard synthesis
        "PHONE_NUMBER": PiiState.Off,  # Keep as-is
        "DATE_TIME": PiiState.GroupingSynthesis,  # LLM grouping synthesis
    }

    response = textual.redact(
        sample_text,
        generator_config=generator_config,
        generator_default=PiiState.Redaction,  # Default for unspecified entities
        random_seed=42
    )

    # Verify Off state - entities kept as-is
    assert "John" in response.redacted_text, "NAME_GIVEN with Off should be preserved"
    assert "555-123-4567" in response.redacted_text, "PHONE_NUMBER with Off should be preserved"

    # Verify Redaction state - tokenized
    assert "Smith" not in response.redacted_text, "NAME_FAMILY should be removed"
    assert "[NAME_FAMILY_" in response.redacted_text, "NAME_FAMILY should be tokenized"
    assert "[LOCATION_ZIP_" in response.redacted_text or "98101" not in response.redacted_text, "ZIP should be tokenized"

    # Verify Synthesis state - replaced but not tokenized
    assert "Acme Corporation" not in response.redacted_text, "ORGANIZATION should be synthesized"
    assert "[ORGANIZATION_" not in response.redacted_text, "ORGANIZATION should not be tokenized"
    assert "john.smith@acme.com" not in response.redacted_text, "EMAIL should be synthesized"
    assert "[EMAIL_ADDRESS_" not in response.redacted_text, "EMAIL should not be tokenized"

    # Verify GroupingSynthesis - LLM-based synthesis
    assert "Seattle" not in response.redacted_text, "LOCATION_CITY should be synthesized"
    assert "[LOCATION_CITY_" not in response.redacted_text, "LOCATION_CITY should not be tokenized"
    assert "January 15, 1990" not in response.redacted_text, "DATE_TIME should be synthesized"
    assert "[DATE_TIME_" not in response.redacted_text, "DATE_TIME should not be tokenized"

    # Verify ReplacementSynthesis - LLM-based synthesis
    assert "WA" not in response.redacted_text, "LOCATION_STATE should be synthesized"
    assert "[LOCATION_STATE_" not in response.redacted_text, "LOCATION_STATE should not be tokenized"

    # Verify we detected entities
    entity_labels = {r.label for r in response.de_identify_results}
    assert len(entity_labels) > 0, "Should detect multiple entity types"

    # Log the result for debugging
    print(f"Original: {sample_text}")
    print(f"Redacted: {response.redacted_text}")
    print(f"Detected entities: {entity_labels}")


def test_synthesis_comparison(textual):
    """Test that grouping synthesis produces different output compared to replacement synthesis."""
    sample_text = (
        "My name is John Smith, and I work for Acme Corporation in Seattle."
    )

    # Fix seed for deterministic comparison
    random_seed = 12345

    # Get results from both methods with different synthesis types
    grouping_config = {
        "NAME_GIVEN": PiiState.GroupingSynthesis,
        "NAME_FAMILY": PiiState.GroupingSynthesis,
        "ORGANIZATION": PiiState.GroupingSynthesis,
        "LOCATION_CITY": PiiState.GroupingSynthesis,
    }

    replacement_config = {
        "NAME_GIVEN": PiiState.ReplacementSynthesis,
        "NAME_FAMILY": PiiState.ReplacementSynthesis,
        "ORGANIZATION": PiiState.ReplacementSynthesis,
        "LOCATION_CITY": PiiState.ReplacementSynthesis,
    }

    grouping_response = textual.redact(
        sample_text, generator_config=grouping_config, random_seed=random_seed
    )

    replacement_response = textual.redact(
        sample_text, generator_config=replacement_config, random_seed=random_seed
    )

    # They should both detect the same entities
    grouping_entities = {(r.label, r.text) for r in grouping_response.de_identify_results}
    replacement_entities = {(r.label, r.text) for r in replacement_response.de_identify_results}
    assert grouping_entities == replacement_entities, (
        "Both methods should detect the same entities"
    )

    # But the synthesized output should be different
    assert grouping_response.redacted_text != replacement_response.redacted_text, (
        "Grouping synthesis should produce different output than replacement synthesis"
    )

    # Grouping output should not contain tokenization patterns
    assert "[" not in grouping_response.redacted_text, (
        "Grouping synthesis should not use tokenization"
    )

    # Replacement output should not contain tokenization patterns
    assert "[" not in replacement_response.redacted_text, (
        "Replacement synthesis should not use tokenization"
    )


@pytest.mark.parametrize("synthesis_state", [PiiState.GroupingSynthesis, PiiState.ReplacementSynthesis])
def test_synthesis_error_handling(textual, synthesis_state):
    """Test error handling in synthesis with invalid parameters."""
    sample_text = "My name is John Smith."

    # Test with invalid generator_default value
    with pytest.raises(Exception) as excinfo:
        textual.redact(sample_text, generator_default="Invalid")
    assert "Invalid value for generator default" in str(excinfo.value)

    # Test with invalid generator_config value
    with pytest.raises(Exception) as excinfo:
        textual.redact(sample_text, generator_config={"NAME_GIVEN": "Invalid"})
    assert "Invalid value for generator config" in str(excinfo.value)

    # Test with empty text
    empty_response = textual.redact("", generator_default=synthesis_state)
    assert empty_response.original_text == "", "Original text should be empty"
    assert len(empty_response.de_identify_results) == 0, (
        "No entities should be detected in empty text"
    )


def test_group_entities_endpoint(textual):
    """Test the group_entities endpoint to verify it returns groups."""
    # Sample text with multiple related entities
    sample_text = (
        "John Smith works at Acme Corporation. "
        "Mr. Smith lives in Seattle. "
        "John's email is john.smith@acme.com."
    )

    # First, get the entities through regular redaction
    response = textual.redact(sample_text)

    # Get the detected entities
    entities = response.de_identify_results

    # Ensure we have entities to group
    assert len(entities) > 0, "No entities were detected in the sample text"

    # Call the group_entities endpoint
    group_response = textual.group_entities(entities, sample_text)

    # Verify we got groups back
    assert group_response is not None, "group_entities should return a response"
    assert hasattr(group_response, 'groups'), "Response should have groups attribute"
    assert len(group_response.groups) > 0, "Should return at least one group"

    # Verify group structure
    for group in group_response.groups:
        assert hasattr(group, 'representative'), "Each group should have a representative"
        assert hasattr(group, 'entities'), "Each group should have entities"
        assert len(group.entities) > 0, "Each group should contain at least one entity"

        # Verify entities in the group are valid
        for entity in group.entities:
            assert hasattr(entity, 'text'), "Entity should have text"
            assert hasattr(entity, 'label'), "Entity should have label"

    # Log basic info about the groups (helpful for debugging)
    print(f"Number of groups created: {len(group_response.groups)}")
    for i, group in enumerate(group_response.groups):
        print(f"Group {i+1}: {group.representative} with {len(group.entities)} entities")

def test_group_entities_endpoint_with_no_entities(textual):
    """Test the group_entities endpoint to verify it returns no groups when we have no entities."""
    # Sample text with multiple related entities
    sample_text = "gddfgjokjoi sfdhjisfoduih qrwehjiihuew"

    # Call the group_entities endpoint
    group_response = textual.group_entities([], sample_text)

    # Verify we got groups back
    assert group_response is not None, "group_entities should return a response"
    assert hasattr(group_response, 'groups'), "Response should have groups attribute"
    assert len(group_response.groups) == 0, "Should return no groups"
