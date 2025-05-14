from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class NameGeneratorMetadata(BaseMetadata):
    def __init__(self, is_consistency_case_sensitive: Optional[bool] = False, preserve_gender: Optional[bool] = False):
        super().__init__()
        self.is_consistency_case_sensitive = is_consistency_case_sensitive if not None else False
        self.preserve_gender = preserve_gender if not None else True

    def to_payload(self, default: "NameGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        result["isConsistencyCaseSensitive"] = self.is_consistency_case_sensitive
        result["preserveGender"] = self.preserve_gender

        return result

default_name_generator_metadata = NameGeneratorMetadata()
def name_generator_metadata_to_payload(metadata: NameGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_name_generator_metadata)