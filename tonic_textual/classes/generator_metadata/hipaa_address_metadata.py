from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class HipaaAddressMetadata(BaseMetadata):
    use_non_hipaa_address_generator: bool
    replace_truncated_zeros_in_zip_code: bool
    realistic_synthetic_values: bool

    def __init__(self):
        super().__init__()
        self.use_non_hipaa_address_generator = False
        self.replace_truncated_zeros_in_zip_code = True
        self.realistic_synthetic_values = True
        
    def __eq__(self, other: "HipaaAddressMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.use_non_hipaa_address_generator != other.use_non_hipaa_address_generator:
            return False

        if self.replace_truncated_zeros_in_zip_code != other.replace_truncated_zeros_in_zip_code:
            return False

        if self.realistic_synthetic_values != other.realistic_synthetic_values:
            return False

        return True
    
    def to_payload(self, default: "HipaaAddressMetadata") -> Dict:
        result = super().to_payload(default)

        if self.use_non_hipaa_address_generator != default.use_non_hipaa_address_generator:
            result["useNonHipaaAddressGenerator"] = self.use_non_hipaa_address_generator

        if self.replace_truncated_zeros_in_zip_code != default.replace_truncated_zeros_in_zip_code:
            result["replaceTruncatedZerosInZipCode"] = self.replace_truncated_zeros_in_zip_code
            
        if self.realistic_synthetic_values != default.realistic_synthetic_values:
            result["realisticSyntheticValues"] = self.realistic_synthetic_values

        return result
    
default_hipaa_address_metadata = HipaaAddressMetadata()
def hipaa_address_metadata_to_payload(metadata: HipaaAddressMetadata) -> Dict:
    return metadata.to_payload(default_hipaa_address_metadata)