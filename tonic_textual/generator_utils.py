from typing import Dict, List, Optional

from tonic_textual.classes.common_api_responses.label_custom_list import LabelCustomList
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.record_api_request_options import RecordApiRequestOptions
from tonic_textual.classes.tonic_exception import BadArgumentsException
from tonic_textual.enums.pii_state import PiiState

default_record_options = RecordApiRequestOptions(False, 0, [])

def utf16len(c):
    """Returns the length of the single character 'c'
    in UTF-16 code units."""
    return 1 if ord(c) < 65536 else 2


def filter_entities_by_config(
    entities: List[SingleDetectionResult],
    generator_config: Dict[str, PiiState],
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


def validate_generator_options(
    generator_default: PiiState, generator_config: Dict[str, PiiState]
) -> None:
    invalid_pii_states = [
        v for v in list(generator_config.values()) if v not in PiiState._member_names_
    ]
    if len(invalid_pii_states) > 0:
        raise Exception(
            "Invalid configuration for generator_config. The allowed values are "
            "Off, Synthesis, and Redaction."
        )
    if generator_default not in PiiState._member_names_:
        raise Exception(
            "Invalid option for generator_default. The allowed values are Off, "
            "Synthesis, and Redaction."
        )

def generate_redact_payload(
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        record_options: RecordApiRequestOptions = default_record_options,
        custom_entities: Optional[List[str]] = None):
        
        validate_generator_options(generator_default, generator_config)
            
        payload = {            
            "generatorDefault": generator_default,
            "generatorConfig": generator_config,
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