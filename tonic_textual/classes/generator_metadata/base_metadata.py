from typing import Dict, Optional

from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseMetadata:
    def __init__(
            self,
            custom_generator: Optional[GeneratorType] = None,
            generator_version: GeneratorVersion = GeneratorVersion.V1
    ):
        self.custom_generator = custom_generator
        self.generator_version = generator_version

    def to_payload(self) -> Dict:
        result = dict()

        result["customGenerator"] = self.custom_generator
        result["generatorVersion"] = self.generator_version

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "BaseMetadata":
        result = BaseMetadata()

        custom_generator_string = payload.get("customGenerator", None)
        if custom_generator_string is not None:
            result.custom_generator = GeneratorType[custom_generator_string]

        result.generator_version = payload.get("generatorVersion", default_base_metadata.generator_version)

        return result

default_base_metadata = BaseMetadata()