from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PhoneNumberGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_us_phone_number_generator: bool = False,
            replace_invalid_numbers: bool = True,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
                custom_generator=GeneratorType.PhoneNumber,
                generator_version=generator_version,
                swaps=swaps
        )
        self["useUsPhoneNumberGenerator"] = use_us_phone_number_generator
        self["replaceInvalidNumbers"] = replace_invalid_numbers

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
            swaps=base_metadata.swaps
        )

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()