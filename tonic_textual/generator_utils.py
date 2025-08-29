from typing import Dict, List, Optional, Union

from tonic_textual.classes.common_api_responses.label_custom_list import LabelCustomList
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.record_api_request_options import RecordApiRequestOptions
from tonic_textual.classes.tonic_exception import BadArgumentsException
from tonic_textual.enums.generator_type import GeneratorType
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import PiiType

default_record_options = RecordApiRequestOptions(False, 0, [])

def utf16len(c):
    """Returns the length of the single character 'c'
    in UTF-16 code units."""
    return 1 if ord(c) < 65536 else 2


def filter_entities_by_config(
    entities: List[SingleDetectionResult],
    generator_config: Dict[str, Union[PiiState, str]],
    generator_default: PiiState,
) -> List[SingleDetectionResult]:
    filtered_entities = []
    for entity in entities:
        if entity["label"] in generator_config:
            if generator_config[entity["label"]] == PiiState.Off:
                continue
        elif generator_default == PiiState.Off:
            continue
        filtered_entities.append(entity)
    return filtered_entities


def make_utf_compatible_entities(
    text: str, entities: List[SingleDetectionResult]
) -> List[Dict]:
    offsets = []
    prev = 0
    for c in text:
        offset = utf16len(c) - 1
        offsets.append(prev + offset)
        prev = prev + offset

    utf_compatible_entities = []
    for entity in entities:
        new_entity = entity.to_dict()
        new_entity["pythonStart"] = entity["start"]
        new_entity["pythonEnd"] = entity["end"]
        new_entity["start"] = entity["start"] + offsets[entity["start"]]
        new_entity["end"] = entity["end"] + offsets[entity["end"] - 1]
        utf_compatible_entities.append(new_entity)

    return utf_compatible_entities


def validate_generator_default_and_config(
    generator_default: Union[PiiState, str],
    generator_config: Dict[str, Union[PiiState, str]],
    custom_entities: Optional[List[str]] = None
) -> None:
    if generator_default not in PiiState._member_names_:
        raise Exception(
            "Invalid value for generator default. "
            "The allowed values are Off, Synthesis, and Redaction."
        )

    invalid_keys = [
        key for key in list(generator_config.keys()) if key not in PiiType._member_names_
    ]

    if custom_entities is not None:
        invalid_keys = [
            key for key in invalid_keys if key not in custom_entities
        ]

    if len(invalid_keys) > 0:
        raise Exception(
            "Invalid key for generator config. "
            "The allowed keys are the supported PII types and any supplied custom entities."
        )

    invalid_values = [
        value for value in list(generator_config.values()) if value not in PiiState._member_names_
    ]
    if len(invalid_values) > 0:
        raise Exception(
            "Invalid value for generator config. "
            "The allowed values are Off, Synthesis, and Redaction."
        )

def convert_payload_to_generator_config(
    payload: Dict = None
) -> Dict[str, PiiState]:
    result = dict()

    if payload is None:
        return result

    for (pii, value) in payload.items():
        for state in PiiState:
            if value == state.value:
                result[pii] = state

    return result

def convert_generator_config_to_payload(
        generator_config: Optional[Dict[str, Union[PiiState, str]]] = None
) -> Dict:
    result = dict()

    if generator_config is None:
        return result

    for (pii, state) in generator_config.items():
        result[pii] = PiiState(state).value # handles the case where state is str or PiiState

    return result


def validate_generator_metadata(
    generator_metadata: Dict[str, BaseMetadata],
    custom_entities: Optional[List[str]] = None
) -> None:
    invalid_keys = [
        key for key in list(generator_metadata.keys()) if key not in PiiType._member_names_
    ]

    if custom_entities is not None:
        invalid_keys = [
            key for key in invalid_keys if key not in custom_entities
        ]

    if len(invalid_keys) > 0:
        raise Exception(
            "Invalid key for generator metadata. "
            "The allowed keys are the supported PII types and any supplied custom entities."
        )

    for (pii, metadata) in generator_metadata.items():
        if (
            pii == PiiType.DATE_TIME or
            pii == PiiType.DOB
        ):
            if not isinstance(metadata, DateTimeGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of DateTimeGeneratorMetadata."
                )

        elif pii == PiiType.PERSON_AGE:
            if not isinstance(metadata, PersonAgeGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of PersonAgeGeneratorMetadata."
                )

        elif (
            pii == PiiType.LOCATION or
            pii == PiiType.LOCATION_ADDRESS or
            pii == PiiType.LOCATION_CITY or
            pii == PiiType.LOCATION_STATE or
            pii == PiiType.LOCATION_ZIP or
            pii == PiiType.LOCATION_COMPLETE_ADDRESS
        ):
            if not isinstance(metadata, HipaaAddressGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of HipaaAddressGeneratorMetadata."
                )

        elif (
            pii == PiiType.PERSON or
            pii == PiiType.NAME_GIVEN or
            pii == PiiType.NAME_FAMILY
        ):
            if not isinstance(metadata, NameGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of NameGeneratorMetadata."
                )

        elif pii == PiiType.PHONE_NUMBER:
            if not isinstance(metadata, PhoneNumberGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of PhoneNumberGeneratorMetadata."
                )

        elif pii == PiiType.NUMERIC_VALUE:
            if not isinstance(metadata, NumericValueGeneratorMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of NumericValueGeneratorMetadata."
                )

        else:
            if not issubclass(type(metadata), BaseMetadata):
                raise Exception(
                    f"Invalid value for generator metadata at {pii}. "
                    "Expected instance of subclass of BaseMetadata."
                )


def convert_generator_metadata_to_payload(
        generator_metadata: Optional[Dict[str, BaseMetadata]] = None
) -> Dict:
    result = dict()

    if generator_metadata is None:
        return result

    for (pii, metadata) in generator_metadata.items():
        result[pii] = metadata.to_payload()

    return result


def convert_payload_to_generator_metadata(
    payload: Dict = None
) -> Dict[str, BaseMetadata]:
    result = dict()

    if payload is None:
        return result

    for pii in [entry.value for entry in PiiType]:
        if (
            pii == PiiType.DATE_TIME or
            pii == PiiType.DOB
        ):
            result[pii] = DateTimeGeneratorMetadata.from_payload(payload.get(pii, dict()))

        elif pii == PiiType.PERSON_AGE:
            result[pii] = PersonAgeGeneratorMetadata.from_payload(payload.get(pii, dict()))

        elif (
            pii == PiiType.LOCATION or
            pii == PiiType.LOCATION_ADDRESS or
            pii == PiiType.LOCATION_CITY or
            pii == PiiType.LOCATION_STATE or
            pii == PiiType.LOCATION_ZIP or
            pii == PiiType.LOCATION_COMPLETE_ADDRESS
        ):
            result[pii] = HipaaAddressGeneratorMetadata.from_payload(payload.get(pii, dict()))

        elif (
            pii == PiiType.PERSON or
            pii == PiiType.NAME_GIVEN or
            pii == PiiType.NAME_FAMILY
        ):
            result[pii] = NameGeneratorMetadata.from_payload(payload.get(pii, dict()))

        elif pii == PiiType.PHONE_NUMBER:
            result[pii] = PhoneNumberGeneratorMetadata.from_payload(payload.get(pii, dict()))

        elif pii == PiiType.NUMERIC_VALUE:
            result[pii] = NumericValueGeneratorMetadata.from_payload(payload.get(pii, dict()))

        else:
            result[pii] = BaseMetadata.from_payload(payload.get(pii, dict()))

    for (pii, metadata) in payload.items():
        if pii not in PiiType._member_names_:
            generator = metadata.get("customGenerator", None)

            if generator == GeneratorType.NumericValue:
                result[pii] = NumericValueGeneratorMetadata.from_payload(metadata)

            elif generator == GeneratorType.Name:
                result[pii] = NameGeneratorMetadata.from_payload(metadata)

            elif generator == GeneratorType.PhoneNumber:
                result[pii] = PhoneNumberGeneratorMetadata.from_payload(metadata)

            elif generator == GeneratorType.HipaaAddressGenerator:
                result[pii] = HipaaAddressGeneratorMetadata.from_payload(metadata)

            elif generator == GeneratorType.PersonAge:
                result[pii] = PersonAgeGeneratorMetadata.from_payload(metadata)

            elif generator == GeneratorType.DateTime:
                result[pii] = DateTimeGeneratorMetadata.from_payload(metadata)

            else:
                result[pii] = BaseMetadata.from_payload(metadata)

    return result

def generate_redact_payload(
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, PiiState] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        record_options: Optional[RecordApiRequestOptions] = None,
        custom_entities: Optional[List[str]] = None
) -> Dict:
        
        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)
            
        payload = {            
            "generatorDefault": generator_default,
            "generatorConfig": convert_generator_config_to_payload(generator_config),
            "generatorMetadata": convert_generator_metadata_to_payload(generator_metadata)
        }

        if custom_entities is not None:
            payload["customPiiEntityIds"] = custom_entities

        if label_block_lists is not None:
            payload["labelBlockLists"] = {
                k: LabelCustomList(regexes=v).to_dict()
                for k, v in label_block_lists.items()
            }
        if label_allow_lists is not None:
            payload["labelAllowLists"] = {
                k: LabelCustomList(regexes=v).to_dict()
                for k, v in label_allow_lists.items()
            }

        if record_options is not None and record_options.record:
            if (
                    record_options.retention_time_in_hours <= 0
                    or record_options.retention_time_in_hours > 720
            ):
                raise BadArgumentsException(
                    "The retention time must be set between 1 and 720 hours"
                )

            record_payload = {
                "retentionTimeInHours": record_options.retention_time_in_hours,
                "tags": record_options.tags,
                "record": True,
            }
            payload["recordApiRequestOptions"] = record_payload
        else:
            payload["recordApiRequestOptions"] = None
        
        return payload

def generate_grouping_playload(replacements: List[Replacement], text: str) -> dict:
    """Construct a grouping request from a list of Replacement objects."""
    entities = [replacement_to_grouping_entity(rep, text) for rep in replacements]
    return {
        "entities": entities,
        "original_text": text
    }

def replacement_to_grouping_entity(replacement: Replacement, text: str) -> dict:
    """Convert a Replacement object to a grouping entity dict with UTF-16 offsets."""
    # Build UTF-16 offset mapping
    offsets = []
    prev = 0
    for i, c in enumerate(text):
        offset = utf16len(c) - 1
        offsets.append(prev + offset)
        prev = prev + offset
    
    # Calculate C# (UTF-16) indices
    csharp_start = replacement.start + offsets[replacement.start]
    csharp_end = replacement.end + offsets[replacement.end - 1]
    
    return {
        "start": csharp_start,             # C# UTF-16 index
        "end": csharp_end,                 # C# UTF-16 index
        "pythonStart": replacement.start,  # Python index
        "pythonEnd": replacement.end,      # Python index
        "label": replacement.label,
        "text": replacement.text,
        "score": replacement.score,
        "language": replacement.language,
        "exampleRedaction": replacement.example_redaction,
        "head": None,
        "tail": None
    }