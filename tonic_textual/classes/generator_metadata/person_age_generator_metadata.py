from typing import Dict, Optional

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class PersonAgeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    """Metadata configuration for person age synthesis.

    Controls how synthesized ages are generated for the ``PERSON_AGE``
    entity type. Ages are shifted by a configurable number of years.

    Parameters
    ----------
    scramble_unrecognized_dates : bool
        When ``True``, dates that Textual cannot parse into a standard
        format are scrambled. Default is ``True``.
    metadata : AgeShiftMetadata
        Configuration for the age shift amount. By default, ages shift by
        7 years.
    use_passthrough_or_group_age_generator : bool
        When ``True`` passes through ages 89 or under. Changes other ages to "90+"
        Default is ``False``
    """

    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            metadata: AgeShiftMetadata = None,
            swaps: Optional[Dict[str,str]] = {},
            constant_value: Optional[str] = None,
            use_passthrough_or_group_age_generator: bool = False,
    ):
        super().__init__(
            custom_generator=GeneratorType.PersonAge,
            generator_version=generator_version,
            scramble_unrecognized_dates=scramble_unrecognized_dates,
            swaps=swaps,
            constant_value=constant_value
        )
        if metadata is None:
            metadata = AgeShiftMetadata()
        self["metadata"] = metadata
        self["usePassthroughOrGroupAgeGenerator"] = use_passthrough_or_group_age_generator

    @property
    def metadata(self) -> AgeShiftMetadata:
        return self["metadata"]

    @metadata.setter
    def metadata(self, value: AgeShiftMetadata):
        self["metadata"] = value

    @property
    def use_passthrough_or_group_age_generator(self) -> bool:
        return self["usePassthroughOrGroupAgeGenerator"]

    @use_passthrough_or_group_age_generator.setter
    def use_passthrough_or_group_age_generator(self, value: bool):
        self["usePassthroughOrGroupAgeGenerator"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "PersonAgeGeneratorMetadata":
        base_metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.PersonAge:
            raise Exception(
                f"Invalid value for custom generator: "
                f"PersonAgeGeneratorMetadata requires {GeneratorType.PersonAge.value} but got {base_metadata.custom_generator}"
            )

        metadata_payload = payload.get("metadata", {})
        age_metadata = AgeShiftMetadata.from_payload(metadata_payload)

        return PersonAgeGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            scramble_unrecognized_dates=base_metadata.scramble_unrecognized_dates,
            metadata=age_metadata,
            swaps=base_metadata.swaps,
            constant_value=base_metadata.constant_value,
            use_passthrough_or_group_age_generator=payload.get("usePassthroughOrGroupAgeGenerator", False)
        )

default_person_age_generator_metadata = PersonAgeGeneratorMetadata()