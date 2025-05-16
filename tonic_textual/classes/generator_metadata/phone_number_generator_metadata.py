from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType


class PhoneNumberGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            use_us_phone_number_generator: Optional[bool] = False,
            replace_invalid_numbers: Optional[bool] = True
    ):
        super().__init__(custom_generator=GeneratorType.PhoneNumber)
        self.use_us_phone_number_generator = use_us_phone_number_generator
        self.replace_invalid_numbers = replace_invalid_numbers
    
    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["useUsPhoneNumberGenerator"] = self.use_us_phone_number_generator
        result["replaceInvalidNumbers"] = self.replace_invalid_numbers

        return result

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()