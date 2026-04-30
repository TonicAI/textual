from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PhoneNumberGeneratorMetadata(BaseMetadata):
    """Metadata configuration for phone number synthesis.

    Controls how synthesized telephone numbers are generated for the
    ``PHONE_NUMBER`` entity type.

    Parameters
    ----------
    use_us_phone_number_generator : bool
        When ``True``, generated telephone numbers use a US phone number format.
        Default is ``False``.
    replace_invalid_numbers : bool
        When ``True``, phone numbers that are detected but are not valid
        phone numbers are replaced with synthesized values. Default
        is ``True``.
    preserve_us_area_code : bool
        When ``True`` and ``use_us_phone_number_generator`` is also ``True``,
        the area code of the original phone number is preserved in the
        synthesized value. Default is ``False``.
    """

    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_us_phone_number_generator: bool = False,
            replace_invalid_numbers: bool = True,
            preserve_us_area_code: bool = False,
            swaps: Optional[Dict[str,str]] = {},
            constant_value: Optional[str] = None,
    ):
        super().__init__(
                custom_generator=GeneratorType.PhoneNumber,
                generator_version=generator_version,
                swaps=swaps,
                constant_value=constant_value
        )
        self["useUsPhoneNumberGenerator"] = use_us_phone_number_generator
        self["replaceInvalidNumbers"] = replace_invalid_numbers
        self["preserveUsAreaCode"] = preserve_us_area_code

    @property
    def use_us_phone_number_generator(self) -> bool:
        return self["useUsPhoneNumberGenerator"]

    @use_us_phone_number_generator.setter
    def use_us_phone_number_generator(self, value: bool):
        self["useUsPhoneNumberGenerator"] = value

    @property
    def replace_invalid_numbers(self) -> bool:
        return self["replaceInvalidNumbers"]

    @replace_invalid_numbers.setter
    def replace_invalid_numbers(self, value: bool):
        self["replaceInvalidNumbers"] = value

    @property
    def preserve_us_area_code(self) -> bool:
        return self["preserveUsAreaCode"]

    @preserve_us_area_code.setter
    def preserve_us_area_code(self, value: bool):
        self["preserveUsAreaCode"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "PhoneNumberGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.PhoneNumber:
            raise Exception(
                f"Invalid value for custom generator: "
                f"PhoneNumberGeneratorMetadata requires {GeneratorType.PhoneNumber.value} but got {base_metadata.custom_generator.name}"
            )

        return PhoneNumberGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            use_us_phone_number_generator=payload.get("useUsPhoneNumberGenerator", False),
            replace_invalid_numbers=payload.get("replaceInvalidNumbers", True),
            preserve_us_area_code=payload.get("preserveUsAreaCode", False),
            swaps=base_metadata.swaps,
            constant_value=base_metadata.constant_value
        )

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()