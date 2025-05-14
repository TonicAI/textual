from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class HipaaAddressGeneratorMetadata(BaseMetadata):
    def __init__(self, use_non_hipaa_address_generator: Optional[bool] = False, replace_truncated_zeros_in_zip_code: Optional[bool] = True, realistic_synthetic_values: Optional[bool] = True):
        super().__init__()
        self.use_non_hipaa_address_generator = use_non_hipaa_address_generator
        self.replace_truncated_zeros_in_zip_code = replace_truncated_zeros_in_zip_code
        self.realistic_synthetic_values = realistic_synthetic_values
    
    def to_payload(self, default: "HipaaAddressGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        result["useNonHipaaAddressGenerator"] = self.use_non_hipaa_address_generator
        result["replaceTruncatedZerosInZipCode"] = self.replace_truncated_zeros_in_zip_code        
        result["realisticSyntheticValues"] = self.realistic_synthetic_values

        return result
    
default_hipaa_address_metadata = HipaaAddressGeneratorMetadata()
def hipaa_address_metadata_to_payload(metadata: HipaaAddressGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_hipaa_address_metadata)