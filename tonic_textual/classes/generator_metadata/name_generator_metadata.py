from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class NameGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            is_consistency_case_sensitive: bool = False,
            preserve_gender: bool = False,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
                custom_generator=GeneratorType.Name,
                generator_version=generator_version,
                swaps=swaps
        )
        self["isConsistencyCaseSensitive"] = is_consistency_case_sensitive
        self["preserveGender"] = preserve_gender

    @property
    def is_consistency_case_sensitive(self) -> bool:
        return self["isConsistencyCaseSensitive"]

    @is_consistency_case_sensitive.setter
    def is_consistency_case_sensitive(self, value: bool):
        self["isConsistencyCaseSensitive"] = value

    @property
    def preserve_gender(self) -> bool:
        return self["preserveGender"]

    @preserve_gender.setter
    def preserve_gender(self, value: bool):
        self["preserveGender"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "NameGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.Name:
            raise Exception(
                f"Invalid value for custom generator: "
                f"NameGeneratorMetadata requires {GeneratorType.Name.value} but got {base_metadata.custom_generator.name}"
            )

        return NameGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            is_consistency_case_sensitive=payload.get("isConsistencyCaseSensitive", False),
            preserve_gender=payload.get("preserveGender", False),
            swaps=base_metadata.swaps
        )

default_name_generator_metadata = NameGeneratorMetadata()