from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType


class NameGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            is_consistency_case_sensitive: Optional[bool] = False,
            preserve_gender: Optional[bool] = False
    ):
        super().__init__(custom_generator=GeneratorType.Name)
        self.is_consistency_case_sensitive = is_consistency_case_sensitive if not None else False
        self.preserve_gender = preserve_gender if not None else True

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["isConsistencyCaseSensitive"] = self.is_consistency_case_sensitive
        result["preserveGender"] = self.preserve_gender

        return result

default_name_generator_metadata = NameGeneratorMetadata()