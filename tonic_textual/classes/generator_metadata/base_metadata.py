from typing import Dict

from tonic_textual.enums.casing import Casing
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseMetadata:
    def __init__(self):
        self.generator_version = GeneratorVersion.V1
        self.custom_generator = None
        self.styles = []
        self.casing = Casing.MixedCase

    def to_payload(self, default: "BaseMetadata") -> Dict:
        result = dict()

        if self.generator_version != default.generator_version:
            result["generatorVersion"] = self.generator_version

        if self.custom_generator != default.custom_generator:
            result["customGenerator"] = self.custom_generator

        if self.styles != default.styles:
            result["styles"] = self.styles

        if self.casing != default.casing:
            result["casing"] = self.casing

        return result

default_base_metadata = BaseMetadata()
def base_metadata_to_payload(metadata: BaseMetadata) -> Dict:
    return metadata.to_payload(default_base_metadata)