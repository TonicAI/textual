from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class HipaaAddressGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_non_hipaa_address_generator: bool = False,
            replace_truncated_zeros_in_zip_code: bool = True,
            realistic_synthetic_values: bool = True
    ):
        super().__init__(
            custom_generator=GeneratorType.HipaaAddressGenerator,
            generator_version=generator_version
        )
        self.use_non_hipaa_address_generator = use_non_hipaa_address_generator
        self.replace_truncated_zeros_in_zip_code = replace_truncated_zeros_in_zip_code
        self.realistic_synthetic_values = realistic_synthetic_values

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["useNonHipaaAddressGenerator"] = self.use_non_hipaa_address_generator
        result["replaceTruncatedZerosInZipCode"] = self.replace_truncated_zeros_in_zip_code
        result["realisticSyntheticValues"] = self.realistic_synthetic_values

        return result
    
    @staticmethod
    def from_payload(payload: Dict) -> "HipaaAddressGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)
        result = HipaaAddressGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.HipaaAddressGenerator:
            raise Exception(
                f"Invalid value for custom generator: "
                f"HipaaAddressGeneratorMetadata requires {GeneratorType.HipaaAddressGenerator.value} but got {result.custom_generator}"
            )

        result.generator_version = base_metadata.generator_version
        result.use_non_hipaa_address_generator = payload.get("useNonHipaaAddressGenerator", default_hipaa_address_generator_metadata.use_non_hipaa_address_generator)
        result.replace_truncated_zeros_in_zip_code = payload.get("replaceTruncatedZerosInZipCode", default_hipaa_address_generator_metadata.replace_truncated_zeros_in_zip_code)
        result.realistic_synthetic_values = payload.get("realisticSyntheticValues",default_hipaa_address_generator_metadata.realistic_synthetic_values)

        return result

default_hipaa_address_generator_metadata = HipaaAddressGeneratorMetadata()