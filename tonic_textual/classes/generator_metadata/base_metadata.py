from typing import Dict, Optional

from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class BaseMetadata(dict):
    def __init__(
            self,
            custom_generator: Optional[GeneratorType] = None,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__()
        self["_type"] = self.__class__.__name__
        self["customGenerator"] = custom_generator
        self["generatorVersion"] = generator_version
        self["swaps"] = swaps if swaps is not None else {}

    @property
    def custom_generator(self) -> Optional[GeneratorType]:
        return self["customGenerator"]

    @custom_generator.setter
    def custom_generator(self, value: Optional[GeneratorType]):
        self["customGenerator"] = value

    @property
    def generator_version(self) -> GeneratorVersion:
        return self["generatorVersion"]

    @generator_version.setter
    def generator_version(self, value: GeneratorVersion):
        self["generatorVersion"] = value

    @property
    def swaps(self) -> Dict[str, str]:
        return self["swaps"]

    @swaps.setter
    def swaps(self, value: Dict[str, str]):
        self["swaps"] = value if value is not None else {}

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "BaseMetadata":
        custom_generator = None
        custom_generator_string = payload.get("customGenerator", None)
        if custom_generator_string is not None:
            if isinstance(custom_generator_string, GeneratorType):
                custom_generator = custom_generator_string
            else:
                custom_generator = GeneratorType[custom_generator_string]

        generator_version_value = payload.get("generatorVersion", GeneratorVersion.V1)
        if isinstance(generator_version_value, GeneratorVersion):
            generator_version = generator_version_value
        else:
            generator_version = GeneratorVersion[generator_version_value]

        swaps = payload.get("swaps", {})

        return BaseMetadata(
            custom_generator=custom_generator,
            generator_version=generator_version,
            swaps=swaps
        )

default_base_metadata = BaseMetadata()