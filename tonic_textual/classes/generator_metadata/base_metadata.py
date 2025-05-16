from typing import Dict, Optional

from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseMetadata:
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            custom_generator: Optional[GeneratorType] = None
    ):
        self.generator_version = generator_version
        self.custom_generator = custom_generator

    def to_payload(self) -> Dict:
        result = dict()

        result["generatorVersion"] = self.generator_version
        result["customGenerator"] = self.custom_generator

        return result

default_base_metadata = BaseMetadata()