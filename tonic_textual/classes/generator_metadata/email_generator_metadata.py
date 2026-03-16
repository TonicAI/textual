from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class EmailGeneratorMetadata(BaseMetadata):
    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            preserve_domain: bool = False,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
                custom_generator=GeneratorType.Email,
                generator_version=generator_version,
                swaps=swaps
        )
        self["preserveDomain"] = preserve_domain

    @property
    def preserve_domain(self) -> bool:
        return self["preserveDomain"]

    @preserve_domain.setter
    def preserve_domain(self, value: bool):
        self["preserveDomain"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "EmailGeneratorMetadata":
        base_metadata = BaseMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.Email:
            raise Exception(
                f"Invalid value for custom generator: "
                f"EmailGeneratorMetadata requires {GeneratorType.Email.value} but got {base_metadata.custom_generator.name}"
            )

        return EmailGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            preserve_domain=payload.get("preserveDomain", False),
            swaps=base_metadata.swaps
        )

default_email_generator_metadata = EmailGeneratorMetadata()
