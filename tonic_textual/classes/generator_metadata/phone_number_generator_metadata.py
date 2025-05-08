from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class PhoneNumberGeneratorMetadata(BaseMetadata):
    use_us_phone_number_generator: bool
    replace_invalid_numbers: bool

    def __init__(self):
        super().__init__()
        self.use_us_phone_number_generator = False
        self.replace_invalid_numbers = True

    def __eq__(self, other: "PhoneNumberGeneratorMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.use_us_phone_number_generator != other.use_us_phone_number_generator:
            return False

        if self.replace_invalid_numbers != other.replace_invalid_numbers:
            return False

        return True
    
    def to_payload(self, default: "PhoneNumberGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        if self.use_us_phone_number_generator != default.use_us_phone_number_generator:
            result["useUsPhoneNumberGenerator"] = self.use_us_phone_number_generator

        if self.replace_invalid_numbers != default.replace_invalid_numbers:
            result["replaceInvalidNumbers"] = self.replace_invalid_numbers

        return result
    

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()
def phone_number_generator_metadata_to_payload(metadata: PhoneNumberGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_phone_number_generator_metadata)