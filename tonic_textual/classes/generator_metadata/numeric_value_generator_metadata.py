from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class NumericValueGeneratorMetadata(BaseMetadata):
    """Metadata configuration for numeric value synthesis.

    Controls how synthesized numeric values are generated for the
    ``NUMERIC_VALUE`` entity type.

    Parameters
    ----------
    use_oracle_integer_pk_generator : bool
        When ``True``, uses a generator designed for Oracle integer primary
        keys. Default is ``False``.
    """

    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            use_oracle_integer_pk_generator: bool = False,
            swaps: Optional[Dict[str,str]] = {},
            constant_value: Optional[str] = None,
    ):
        super().__init__(
            custom_generator=GeneratorType.NumericValue,
            generator_version=generator_version,
            swaps=swaps,
            constant_value=constant_value
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
            swaps=base_metadata.swaps,
            constant_value=base_metadata.constant_value
        )

default_numeric_value_generator_metadata = NumericValueGeneratorMetadata()