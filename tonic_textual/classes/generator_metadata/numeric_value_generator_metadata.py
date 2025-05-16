from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType

class NumericValueGeneratorMetadata(BaseMetadata):
    def __init__(self, use_oracle_integer_pk_generator: Optional[bool] = False):
        super().__init__(custom_generator=GeneratorType.NumericValue)
        self.use_oracle_integer_pk_generator = use_oracle_integer_pk_generator

    def to_payload(self) -> Dict:
        result = super().to_payload()

        result["useOracleIntegerPkGenerator"] = self.use_oracle_integer_pk_generator

        return result