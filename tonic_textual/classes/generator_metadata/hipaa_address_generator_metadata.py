from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class HipaaAddressGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_non_hipaa_address_generator: bool = False,
            replace_truncated_zeros_in_zip_code: bool = True,
            realistic_synthetic_values: bool = True,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
            custom_generator=GeneratorType.HipaaAddressGenerator,
            generator_version=generator_version,
            swaps=swaps
        )
        self["useNonHipaaAddressGenerator"] = use_non_hipaa_address_generator
        self["replaceTruncatedZerosInZipCode"] = replace_truncated_zeros_in_zip_code
        self["realisticSyntheticValues"] = realistic_synthetic_values

    @property
    def use_non_hipaa_address_generator(self) -> bool:
        return self["useNonHipaaAddressGenerator"]

    @use_non_hipaa_address_generator.setter
    def use_non_hipaa_address_generator(self, value: bool):
        self["useNonHipaaAddressGenerator"] = value

    @property
    def replace_truncated_zeros_in_zip_code(self) -> bool:
        return self["replaceTruncatedZerosInZipCode"]

    @replace_truncated_zeros_in_zip_code.setter
    def replace_truncated_zeros_in_zip_code(self, value: bool):
        self["replaceTruncatedZerosInZipCode"] = value

    @property
    def realistic_synthetic_values(self) -> bool:
        return self["realisticSyntheticValues"]

    @realistic_synthetic_values.setter
    def realistic_synthetic_values(self, value: bool):
        self["realisticSyntheticValues"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "HipaaAddressGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.HipaaAddressGenerator:
            raise Exception(
                f"Invalid value for custom generator: "
                f"HipaaAddressGeneratorMetadata requires {GeneratorType.HipaaAddressGenerator.value} but got {base_metadata.custom_generator}"
            )

        return HipaaAddressGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            use_non_hipaa_address_generator=payload.get("useNonHipaaAddressGenerator", False),
            replace_truncated_zeros_in_zip_code=payload.get("replaceTruncatedZerosInZipCode", True),
            realistic_synthetic_values=payload.get("realisticSyntheticValues", True),
            swaps=base_metadata.swaps
        )

default_hipaa_address_generator_metadata = HipaaAddressGeneratorMetadata()