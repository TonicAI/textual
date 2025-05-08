from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class NameGeneratorMetadata(BaseMetadata):
    is_consistency_case_sensitive: bool
    preserve_gender: bool

    def __init__(self):
        super().__init__()
        self.is_consistency_case_sensitive = False
        self.preserve_gender = False

    def __eq__(self, other: "NameGeneratorMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.is_consistency_case_sensitive != other.is_consistency_case_sensitive:
            return False

        if self.preserve_gender != other.preserve_gender:
            return False

        return True

    def to_payload(self, default: "NameGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        if self.is_consistency_case_sensitive != default.is_consistency_case_sensitive:
            result["isConsistencyCaseSensitive"] = self.is_consistency_case_sensitive

        if self.preserve_gender != default.preserve_gender:
            result["preserveGender"] = self.preserve_gender

        return result

default_name_generator_metadata = NameGeneratorMetadata()
def name_generator_metadata_to_payload(metadata: NameGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_name_generator_metadata)