from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class NumericValueGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_oracle_integer_pk_generator: bool = False
    ):
        super().__init__(
            custom_generator=GeneratorType.NumericValue,
            generator_version=generator_version
        )
        self.use_oracle_integer_pk_generator = use_oracle_integer_pk_generator

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["useOracleIntegerPkGenerator"] = self.use_oracle_integer_pk_generator

        return result

    @staticmethod
    def from_payload(payload: Dict) -> "NumericValueGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)
        result = NumericValueGeneratorMetadata()

        result.custom_generator = base_metadata.custom_generator
        if result.custom_generator is not GeneratorType.NumericValue:
            raise Exception(
                f"Invalid value for custom generator: "
                f"NumericValueGeneratorMetadata requires {GeneratorType.NumericValue.value} but got {result.custom_generator.name}"
            )

        result.generator_version = base_metadata.generator_version
        result.use_oracle_integer_pk_generator = payload.get("useOracleIntegerPkGenerator", default_numeric_value_generator_metadata.use_oracle_integer_pk_generator)

        return result

default_numeric_value_generator_metadata = NumericValueGeneratorMetadata()