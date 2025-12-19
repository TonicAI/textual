from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class NumericValueGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_oracle_integer_pk_generator: bool = False,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
            custom_generator=GeneratorType.NumericValue,
            generator_version=generator_version,
            swaps=swaps
        )
        self["useOracleIntegerPkGenerator"] = use_oracle_integer_pk_generator

    @property
    def use_oracle_integer_pk_generator(self) -> bool:
        return self["useOracleIntegerPkGenerator"]

    @use_oracle_integer_pk_generator.setter
    def use_oracle_integer_pk_generator(self, value: bool):
        self["useOracleIntegerPkGenerator"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "NumericValueGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.NumericValue:
            raise Exception(
                f"Invalid value for custom generator: "
                f"NumericValueGeneratorMetadata requires {GeneratorType.NumericValue.value} but got {base_metadata.custom_generator.name}"
            )

        return NumericValueGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            use_oracle_integer_pk_generator=payload.get("useOracleIntegerPkGenerator", False),
            swaps=base_metadata.swaps
        )

default_numeric_value_generator_metadata = NumericValueGeneratorMetadata()