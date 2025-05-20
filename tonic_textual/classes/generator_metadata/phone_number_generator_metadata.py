from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PhoneNumberGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_us_phone_number_generator: bool = False,
            replace_invalid_numbers: bool = True
    ):
        super().__init__(
                custom_generator=GeneratorType.PhoneNumber,
                generator_version=generator_version
        )
        self.use_us_phone_number_generator = use_us_phone_number_generator
        self.replace_invalid_numbers = replace_invalid_numbers
    
    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["useUsPhoneNumberGenerator"] = self.use_us_phone_number_generator
        result["replaceInvalidNumbers"] = self.replace_invalid_numbers

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "PhoneNumberGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)
        result = PhoneNumberGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.PhoneNumber:
            raise Exception(
                f"Invalid value for custom generator: "
                f"PhoneNumberGeneratorMetadata requires {GeneratorType.PhoneNumber.value} but got {result.custom_generator.name}"
            )

        result.generator_version = base_metadata.generator_version
        result.use_us_phone_number_generator = payload.get("useUsPhoneNumberGenerator", default_phone_number_generator_metadata.use_us_phone_number_generator)
        result.replace_invalid_numbers = payload.get("replaceInvalidNumbers", default_phone_number_generator_metadata.replace_invalid_numbers)

        return result

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()