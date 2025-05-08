from typing import Dict

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata


class NumericValueGeneratorMetadata(BaseMetadata):
    use_oracle_integer_pk_generator: bool

    def __init__(self):
        super().__init__()
        self.use_oracle_integer_pk_generator = False

    def __eq__(self, other: "NumericValueGeneratorMetadata") -> bool:
        if not super().__eq__(other):
            return False

        if self.use_oracle_integer_pk_generator != other.use_oracle_integer_pk_generator:
            return False

        return True

    def to_payload(self, default: "NumericValueGeneratorMetadata") -> Dict:
        result = super().to_payload(default)

        if self.use_oracle_integer_pk_generator != default.use_oracle_integer_pk_generator:
            result["useOracleIntegerPkGenerator"] = self.use_oracle_integer_pk_generator

        return result


default_numeric_value_generator_metadata = NumericValueGeneratorMetadata()
def numeric_value_generator_metadata_to_payload(metadata: NumericValueGeneratorMetadata) -> Dict:
    return metadata.to_payload(default_numeric_value_generator_metadata)