from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class PhoneNumberGeneratorMetadata(BaseMetadata):
    def __init__(self, use_us_phone_number_generator: Optional[bool] = False, replace_invalid_numbers: Optional[bool] = True):
        super().__init__()
        self.use_us_phone_number_generator = use_us_phone_number_generator
        self.replace_invalid_numbers = replace_invalid_numbers
    
    def to_payload(self, default: "PhoneNumberGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        result["useUsPhoneNumberGenerator"] = self.use_us_phone_number_generator
        result["replaceInvalidNumbers"] = self.replace_invalid_numbers

        return result
    

default_phone_number_generator_metadata = PhoneNumberGeneratorMetadata()
def phone_number_generator_metadata_to_payload(metadata: PhoneNumberGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_phone_number_generator_metadata)