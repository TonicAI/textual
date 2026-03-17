from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.email_generator_metadata import EmailGeneratorMetadata
from tonic_textual.redact_api import TextualNer


def test_structured_email_preserve_domain(textual: TextualNer):
    emails = ["john@example.com", "jane@company.org"]

    result = textual.redact_structured(
        emails,
        pii_type="EMAIL_ADDRESS",
        generator_metadata=EmailGeneratorMetadata(preserve_domain=True),
        random_seed=42,
    )

    assert len(result) == 2
    assert result[0].endswith("@example.com"), f"Expected domain preserved, got: '{result[0]}'"
    assert result[1].endswith("@company.org"), f"Expected domain preserved, got: '{result[1]}'"
    assert result[0] != "john@example.com", "Local part should be scrambled"


def test_structured_email_without_metadata_scrambles_domain(textual: TextualNer):
    emails = ["john@example.com"]

    result = textual.redact_structured(
        emails,
        pii_type="EMAIL_ADDRESS",
        random_seed=42,
    )

    assert len(result) == 1
    assert not result[0].endswith("@example.com"), f"Without metadata, domain should be scrambled, got: '{result[0]}'"


def test_structured_deterministic_with_seed(textual: TextualNer):
    emails = ["john@example.com", "jane@company.org"]
    metadata = EmailGeneratorMetadata(preserve_domain=True)

    result1 = textual.redact_structured(emails, pii_type="EMAIL_ADDRESS", generator_metadata=metadata, random_seed=42)
    result2 = textual.redact_structured(emails, pii_type="EMAIL_ADDRESS", generator_metadata=metadata, random_seed=42)

    assert result1[0] == result2[0], "Same seed should produce same output"
    assert result1[1] == result2[1], "Same seed should produce same output"


def test_structured_swap_metadata(textual: TextualNer):
    result = textual.redact_structured(
        ["Acme"],
        pii_type="ORGANIZATION",
        generator_metadata=BaseMetadata(swaps={"Acme": "Contoso"}),
        random_seed=42,
    )

    assert len(result) == 1
    assert result[0] == "Contoso", f"Swap should replace 'Acme' with 'Contoso', got: '{result[0]}'"
