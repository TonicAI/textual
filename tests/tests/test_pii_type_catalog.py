from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import DeprecatedPiiType, PiiType
from tonic_textual.generator_utils import validate_generator_default_and_config


def test_current_solar_pii_types_are_valid_generator_config_keys():
    current_types = [
        PiiType.ACCOUNT_NUMBER,
        PiiType.DRIVERS_LICENSE_NUMBER,
        PiiType.VEHICLE_ID,
    ]

    validate_generator_default_and_config(
        PiiState.Redaction,
        {pii_type.name: PiiState.Redaction for pii_type in current_types},
    )


def test_username_is_not_deprecated():
    assert "USERNAME" not in DeprecatedPiiType._member_names_
