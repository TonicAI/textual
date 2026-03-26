from typing import List, Dict, Optional

from tonic_textual.classes.generator_metadata.base_date_time_generator_metadata import BaseDateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.generator_version import GeneratorVersion


class DateTimeGeneratorMetadata(BaseDateTimeGeneratorMetadata):
    """Metadata configuration for date and time synthesis.

    Controls how synthesized date and time values are generated for the
    ``DATE_TIME`` entity type. Dates are shifted by a random number of days
    within a configurable range.

    Parameters
    ----------
    scramble_unrecognized_dates : bool
        When ``True``, dates that Textual cannot parse into a standard
        format are still scrambled. Default is ``True``.
    additional_date_formats : list of str
        A list of additional date format patterns that Textual should
        recognize. Use Python ``strftime``/``strptime`` format codes.
        Default is an empty list.
    apply_constant_shift_to_document : bool
        When ``True``, all dates within the same document are shifted by
        the same random offset, preserving relative time differences
        between dates. Default is ``False``.
    metadata : TimestampShiftMetadata
        Configuration for the date shift range. Default shifts dates by
        -7 to +7 days.
    """

    def __init__(
            self,
            generator_version: GeneratorVersion = GeneratorVersion.V1,
            scramble_unrecognized_dates: bool = True,
            additional_date_formats: List[str] = list(),
            apply_constant_shift_to_document: bool = False,
            metadata: TimestampShiftMetadata = None,
            swaps: Optional[Dict[str,str]] = {}
    ):
        super().__init__(
            custom_generator=GeneratorType.DateTime,
            generator_version=generator_version,
            scramble_unrecognized_dates=scramble_unrecognized_dates,
            swaps=swaps
        )
        if metadata is None:
            metadata = TimestampShiftMetadata()
        self["metadata"] = metadata
        self["additionalDateFormats"] = additional_date_formats
        self["applyConstantShiftToDocument"] = apply_constant_shift_to_document

    @property
    def metadata(self) -> TimestampShiftMetadata:
        return self["metadata"]

    @metadata.setter
    def metadata(self, value: TimestampShiftMetadata):
        self["metadata"] = value

    @property
    def additional_date_formats(self) -> List[str]:
        return self["additionalDateFormats"]

    @additional_date_formats.setter
    def additional_date_formats(self, value: List[str]):
        self["additionalDateFormats"] = value

    @property
    def apply_constant_shift_to_document(self) -> bool:
        return self["applyConstantShiftToDocument"]

    @apply_constant_shift_to_document.setter
    def apply_constant_shift_to_document(self, value: bool):
        self["applyConstantShiftToDocument"] = value

    def to_payload(self) -> Dict:
        return dict(self)

    @staticmethod
    def from_payload(payload: Dict) -> "DateTimeGeneratorMetadata":
        base_metadata = BaseDateTimeGeneratorMetadata.from_payload(payload)

        if base_metadata.custom_generator is not GeneratorType.DateTime:
            raise Exception(
                f"Invalid value for custom generator: "
                f"DateTimeGeneratorMetadata requires {GeneratorType.DateTime.value} but got {base_metadata.custom_generator.name}"
            )

        metadata_payload = payload.get("metadata", {})
        ts_metadata = TimestampShiftMetadata.from_payload(metadata_payload)

        return DateTimeGeneratorMetadata(
            generator_version=base_metadata.generator_version,
            scramble_unrecognized_dates=base_metadata.scramble_unrecognized_dates,
            additional_date_formats=payload.get("additionalDateFormats", []),
            apply_constant_shift_to_document=payload.get("applyConstantShiftToDocument", False),
            metadata=ts_metadata,
            swaps=base_metadata.swaps
        )

default_date_time_generator_metadata = DateTimeGeneratorMetadata()
