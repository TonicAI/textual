from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class HipaaAddressGeneratorMetadata(BaseMetadata):
    """Metadata configuration for HIPAA-compliant address synthesis.

    Controls how synthesized addresses are generated for location entity
    types such as ``LOCATION_ADDRESS`` and ``LOCATION_ZIP``. By default,
    address synthesis follows HIPAA Safe Harbor de-identification rules.

    Parameters
    ----------
    use_non_hipaa_address_generator : bool
        When ``True``, uses a non-HIPAA-compliant address generator that
        may produce more realistic addresses, but does not guarantee HIPAA
        Safe Harbor compliance. Default is ``False``.
    replace_truncated_zeros_in_zip_code : bool
        When ``True``, for ZIP codes that are truncated to three digits
        (per HIPAA Safe Harbor), the removed digits are replaced with
        zeros. Default is ``True``.
    realistic_synthetic_values : bool
        When ``True``, generates realistic-looking synthetic address values.
        Default is ``True``.
    use_three_digit_zips : bool
        When ``True`` zip codes are always truncated to three digits.
        Default is ``False``
    replace_foreign_zip_codes_with_zeros : bool
        When ``True`` foreign zip codes become all zeros
        Default is ``False``
    """

    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_non_hipaa_address_generator: bool = False,
            replace_truncated_zeros_in_zip_code: bool = True,
            realistic_synthetic_values: bool = True,
            swaps: Optional[Dict[str,str]] = {},
            constant_value: Optional[str] = None,
            use_three_digit_zips: bool = False,
            replace_foreign_zip_codes_with_zeros: bool = False,
    ):
        super().__init__(
            custom_generator=GeneratorType.HipaaAddressGenerator,
            generator_version=generator_version,
            swaps=swaps,
            constant_value=constant_value
        )
        self["useNonHipaaAddressGenerator"] = use_non_hipaa_address_generator
        self["replaceTruncatedZerosInZipCode"] = replace_truncated_zeros_in_zip_code
        self["realisticSyntheticValues"] = realistic_synthetic_values
        self["useThreeDigitZips"] = use_three_digit_zips
        self["replaceForeignZipCodesWithZeros"] = replace_foreign_zip_codes_with_zeros

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

    @property
    def use_three_digit_zips(self) -> bool:
        return self["useThreeDigitZips"]

    @use_three_digit_zips.setter
    def use_three_digit_zips(self, value: bool):
        self["useThreeDigitZips"] = value

    @property
    def replace_foreign_zip_codes_with_zeros(self) -> bool:
        return self["replaceForeignZipCodesWithZeros"]

    @replace_foreign_zip_codes_with_zeros.setter
    def replace_foreign_zip_codes_with_zeros(self, value: bool):
        self["replaceForeignZipCodesWithZeros"] = value

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
            swaps=base_metadata.swaps,
            constant_value=base_metadata.constant_value,
            use_three_digit_zips=payload.get("useThreeDigitZips", False),
            replace_foreign_zip_codes_with_zeros=payload.get("replaceForeignZipCodesWithZeros", False)
        )

default_hipaa_address_generator_metadata = HipaaAddressGeneratorMetadata()