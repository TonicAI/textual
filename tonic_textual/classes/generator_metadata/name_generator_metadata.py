from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class NameGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            is_consistency_case_sensitive: bool = False,
            preserve_gender: bool = False
    ):
        super().__init__(
                custom_generator=GeneratorType.Name,
                generator_version=generator_version
        )
        self.is_consistency_case_sensitive = is_consistency_case_sensitive
        self.preserve_gender = preserve_gender

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["isConsistencyCaseSensitive"] = self.is_consistency_case_sensitive
        result["preserveGender"] = self.preserve_gender

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "NameGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)
        result = NameGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.Name:
            raise Exception(
                f"Invalid value for custom generator: "
                f"NameGeneratorMetadata requires {GeneratorType.Name.value} but got {result.custom_generator.name}"
            )

        result.generator_version = base_metadata.generator_version
        result.is_consistency_case_sensitive = payload.get("isConsistencyCaseSensitive", default_name_generator_metadata.is_consistency_case_sensitive)
        result.preserve_gender = payload.get("preserveGender", default_name_generator_metadata.preserve_gender)

        return result

default_name_generator_metadata = NameGeneratorMetadata()