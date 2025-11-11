import io
import json
import os
from time import sleep
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode
from warnings import warn
import requests
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.classes.generator_metadata.base_metadata import BaseMetadata
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.llm_synthesis.llm_grouping_models import GroupResponse, LlmGrouping
from tonic_textual.classes.record_api_request_options import RecordApiRequestOptions
from tonic_textual.classes.redact_api_responses.bulk_redaction_response import (
    BulkRedactionResponse,
)
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)
from tonic_textual.classes.tonic_exception import (
    DatasetNameAlreadyExists,
    FileNotReadyForDownload,
    InvalidJsonForRedactionRequest,
)
from tonic_textual.classes.audio.redact_audio_responses import (
    TranscriptionResult
)
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.generator_utils import generate_grouping_playload, validate_generator_default_and_config, default_record_options, \
    generate_redact_payload, validate_generator_metadata
from tonic_textual.services.dataset import DatasetService
from tonic_textual.services.datasetfile import DatasetFileService

class TextualNer:
    """Wrapper class to invoke the Tonic Textual API

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes. The default value is https://textual.tonic.ai.
    api_key : str
        Optional. Your API token. Instead of providing the API token
        here, we recommended that you set the API key in your environment as the
        value of TONIC_TEXTUAL_API_KEY.
    verify: bool
        Whether to verify SSL certification. By default, this is enabled.
    Examples
    --------
    >>> from tonic_textual.redact_api import TextualNer
    >>> textual = TextualNer()
    """

    def __init__(
        self,
        base_url: str = "https://textual.tonic.ai",
        api_key: Optional[str] = None,
        verify: bool = True,
    ):
        if api_key is None:
            api_key = os.environ.get("TONIC_TEXTUAL_API_KEY")
            if api_key is None:
                raise Exception(
                    "No API key provided. Either provide an API key, or set the API "
                    "key as the value of the TONIC_TEXTUAL_API_KEY environment "
                    "variable."
                )

        self.api_key = api_key
        self.client = HttpClient(base_url, self.api_key, verify)
        self.dataset_service = DatasetService(self.client)
        self.datasetfile_service = DatasetFileService(self.client)
        self.verify = verify

    def create_dataset(self, dataset_name: str):
        """Creates a dataset. A dataset is a collection of 1 or more files for Tonic
        Textual to scan and redact.

        Parameters
        -----
        dataset_name : str
            The name of the dataset. Dataset names must be unique.


        Returns
        -------
        Dataset
            The newly created dataset.


        Raises
        ------

        DatasetNameAlreadyExists
            Raised if a dataset with the same name already exists.

        """

        try:
            self.client.http_post("/api/dataset", data={"name": dataset_name})
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise DatasetNameAlreadyExists(e)

        return self.get_dataset(dataset_name)

    def delete_dataset(self, dataset_name: str):
        """Deletes dataset by name.

        Parameters
        -----
        dataset_name : str
            The name of the dataset to delete.
        """

        params = {"datasetName": dataset_name}
        self.client.http_delete(
            "/api/dataset/delete_dataset_by_name?" + urlencode(params)
        )

    def get_dataset(self, dataset_name: str) -> Dataset:
        """Gets the dataset for the specified dataset name.

        Parameters
        ----------
        dataset_name : str
            The name of the dataset.

        Returns
        -------
        Dataset

        Examples
        --------
        >>> dataset = tonic.get_dataset("llama_2_chatbot_finetune_v5")
        """

        return self.dataset_service.get_dataset(dataset_name)

    def get_all_datasets(self) -> List[Dataset]:
        """Gets all of the user's datasets

        Returns
        -------
        List[Dataset]
            The list of all datasets

        Examples
        --------
        >>> datasets = tonic.get_all_datasets()
        """
        return self.dataset_service.get_all_datasets()

    def get_files(self, dataset_id: str) -> List[DatasetFile]:
        """
        Gets all of the files in the dataset.

        Returns
        ------
        List[DatasetFile]
            A list of all of the files in the dataset.
        """

        return self.datasetfile_service.get_files(dataset_id)

    def unredact_bulk(
        self, redacted_strings: List[str], random_seed: Optional[int] = None
    ) -> List[str]:
        """Removes redaction from a list of strings. Returns the strings with the
        original values.

        Parameters
        ----------
        redacted_strings : List[str]
            The list of redacted strings from which to remove the redaction.

        random_seed: Optional[int] = None
            Ann optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        Returns
        -------
        List[str]
            The list of strings with the redaction removed.
        """

        if random_seed is not None:
            additional_headers = {"textual-random-seed": str(random_seed)}
        else:
            additional_headers = {}

        response = self.client.http_post(
            "/api/unredact",
            data=redacted_strings,
            additional_headers=additional_headers,
        )
        return response

    def unredact(self, redacted_string: str, random_seed: Optional[int] = None) -> str:
        """Removes the redaction from a provided string. Returns the string with the
        original values.

        Parameters
        ----------
        redacted_string : str
            The redacted string from which to remove the redaction.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        Returns
        -------
        str
            The string with the redaction removed.
        """

        if random_seed is not None:
            additional_headers = {"textual-random-seed": str(random_seed)}
        else:
            additional_headers = {}

        response = self.client.http_post(
            "/api/unredact",
            data=[redacted_string],
            additional_headers=additional_headers,
        )

        return response

    def redact_audio(
        self,
        file_path: str,
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, PiiState] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
        num_retries: Optional[int] = 30,
        wait_between_retries: Optional[int] = 10,
    ) -> RedactionResponse:
        warn(
            "This method is deprecated. Instead, use a combination of get_audio_transcription and redact_audio_transcription from the TextualAudio module.",
            DeprecationWarning,
            stacklevel=1,
        )
    
    def get_audio_transcription(
        self,
        file_path: str,            
        num_retries: Optional[int] = 30,
        wait_between_retries: Optional[int] = 10,
    ) -> TranscriptionResult:
        warn(
            "This method is deprecated. Instead, use the identical method in the TextualAudio module.",
            DeprecationWarning,
            stacklevel=1,
        )
    
    def redact_audio_file(
        self,
        audio_file_path: str,
        output_file_path: str,
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, PiiState] = dict(),
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
        before_beep_buffer: float = 250.0,
        after_beep_buffer: float = 250.0
    ):
        """Generates a redacted audio file by identifying and removing sensitive audio segments.

        Parameters
        ----------
        audio_file_path : str
            The path to the input audio file.
            Supported file types are wav, mp3, ogg, flv, wma, aac, and others. See
            https://github.com/jiaaro/pydub for complete information on file types
            supported.

        output_file_path : str
            The path to save the redacted output file. The output file path specifies
            the audio file type that the output is written as via it's extension.
            Supported file types are wav, mp3, ogg, flv, wma, and aac. See
            https://github.com/jiaaro/pydub for complete information on file types
            supported.
        
        generator_default: PiiState = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".
            
        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of
            text matches a listed regular expression, the text is marked as the
            entity type and is included in the redaction or synthesis.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        before_beep_buffer : float, optional
            Buffer time (in milliseconds) to include before redaction interval
            (default is 250.0).

        after_beep_buffer : float, optional
            Buffer time (in milliseconds) to include after redaction interval
            (default is 250.0).

        Returns
        -------
        str
            The path to the redacted output audio file.
        """
        warn(
            "This method is deprecated. Instead, use the identical method in the TextualAudio module.",
            DeprecationWarning,
            stacklevel=1,
        )        
    
    def redact(
        self,
        string: str,
        generator_default: PiiState = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        record_options: RecordApiRequestOptions = default_record_options,
        custom_entities: Optional[List[str]] = None,
    ) -> RedactionResponse:
        """Redacts a string. Depending on the configured handling for each sensitive
        data type, values are either redacted, synthesized, or ignored.

        Parameters
        ----------
        string : str
            The string to redact.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random
            number seeding. Can be used to ensure that different API calls use
            the same or different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of
            text matches a listed regular expression, the text is marked as the
            entity type and is included in the redaction or synthesis.

        record_options: RecordApiRequestOptions
            A value to record the API request and results for analysis in the
            Textual application. The default value is to not record the API
            request.  Must specify a time between 1 and 720 hours (inclusive).

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        RedactionResponse
            The redacted string along with ancillary information.

        Examples
        --------
            >>> textual.redact(
            >>>     "John Smith is a person",
            >>>     # only redacts NAME_GIVEN
            >>>     generator_config={"NAME_GIVEN": "Redaction", "CUSTOM_COGNITIVE_ACCESS_KEY": "Synthesis"},
            >>>     generator_default="Off",
            >>>     # Occurrences of "There" are treated as NAME_GIVEN entities
            >>>     label_allow_lists={"NAME_GIVEN": ["There"]},
            >>>     # Text matching the regex ` ([a-z]{2}) ` is not treated as an occurrence of NAME_FAMILY
            >>>     label_block_lists={"NAME_FAMILY": [" ([a-z]{2}) "]},
            >>>     # The custom entities passed here will be included in the redaction and may be included in generator_config
            >>>     custom_entities=["CUSTOM_COGNITIVE_ACCESS_KEY", "CUSTOM_PERSONAL_GRAVITY_INDEX"],
            >>> )


        """

        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            label_allow_lists,
            record_options,
            custom_entities
        )

        payload["text"] = string

        return self.send_redact_request("/api/redact", payload, random_seed)

    def redact_bulk(
        self,
        strings: List[str],
        generator_default: Union[PiiState, str] = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
    ) -> BulkRedactionResponse:
        """Redacts a string. Depending on the configured handling for each sensitive
        data type, values are either redacted, synthesized, or ignored.

        Parameters
        ----------
        strings : List[str]
            The array of strings to redact.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random
            number seeding. Can be used to ensure that different API calls use
            the same or different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of
            text matches a listed regular expression, the text is marked as the
            entity type and is included in the redaction or synthesis.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        RedactionResponse
            The redacted string along with ancillary information.

        Examples
        --------
            >>> textual.redact_bulk(
            >>>     ["John Smith is a person", "I live in Atlanta"],
            >>>     # only redacts NAME_GIVEN
            >>>     generator_config={"NAME_GIVEN": "Redaction", "CUSTOM_COGNITIVE_ACCESS_KEY": "Synthesis"},
            >>>     generator_default="Off",
            >>>     # Occurrences of "There" are treated as NAME_GIVEN entities
            >>>     label_allow_lists={"NAME_GIVEN": ["There"]},
            >>>     # Text matching the regex ` ([a-z]{2}) ` is not treated as an occurrence of NAME_FAMILY
            >>>     label_block_lists={"NAME_FAMILY": [" ([a-z]{2}) "]},
            >>>     # The custom entities passed here will be included in the redaction and may be included in generator_config
            >>>     custom_entities=["CUSTOM_COGNITIVE_ACCESS_KEY", "CUSTOM_PERSONAL_GRAVITY_INDEX"],
            >>> )
        """

        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)

        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            label_allow_lists,
            None,
            custom_entities
        )
        payload["bulkText"] = strings

        return self.send_redact_bulk_request("/api/redact/bulk", payload, random_seed)
    
    def group_entities(self, ner_entities: list[Replacement], original_text: str) -> GroupResponse:
        payload = generate_grouping_playload(ner_entities, original_text)

        # Send request to the correct endpoint
        response = self.client.http_post("/api/synthesis/group", data=payload)
        
        # Parse response and create GroupResponse with LlmGrouping objects
        groups = []
        for group in response.get("groups", []):
            group_entities = []
            for entity_data in group.get("entities", []):
                # Convert camelCase fields to snake_case for Replacement
                group_entities.append(Replacement(
                    start=entity_data.get("start"),
                    end=entity_data.get("end"),
                    new_start=entity_data.get("newStart", entity_data.get("start")),
                    new_end=entity_data.get("newEnd", entity_data.get("end")),
                    label=entity_data.get("label"),
                    text=entity_data.get("text"),
                    score=entity_data.get("score"),
                    language=entity_data.get("language"),
                    new_text=entity_data.get("newText"),
                    example_redaction=entity_data.get("exampleRedaction")
                ))
            
            groups.append(
                LlmGrouping(
                    representative=group.get("representative"),
                    entities=group_entities
                )
            )
        
        return GroupResponse(groups=groups)
    

    def redact_json(
        self,
        json_data: Union[str, dict],
        generator_default: Union[PiiState, str] = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        jsonpath_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
    ) -> RedactionResponse:
        """Redacts the values in a JSON blob. Depending on the configured handling for
        each sensitive data type, values are either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        json_data : Union[str, dict]
            The JSON for which to redact values. This can be either a JSON string
            or a Python dictionary.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for the entity type matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.

        jsonpath_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, path expression). When an element in the JSON document matches the JSON path expression, the entire text value is treated as the specified entity type.
            Only supported for path expressions that point to JSON primitive values. This setting overrides any results found by the NER model or in label allow and block lists.
            If multiple path expressions point to the same JSON node, but specify different entity types, then the value is redacted as one of those types. However, the chosen type is selected at random - it could use any of the types.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        RedactionResponse
            The redacted string along with ancillary information.
        """

        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)

        if isinstance(json_data, str):
            json_text = json_data
        elif isinstance(json_data, dict):
            json_text = json.dumps(json_data)
        else:
            raise Exception(
                "redact_json must receive either a JSON blob as a string or dict(). "
                f"You passed in type {type(json_data)} which is not supported"
            )

        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            label_allow_lists,
            None,
            custom_entities
        )
        payload["jsonText"] = json_text

        if jsonpath_allow_lists is not None:
            payload["jsonPathAllowLists"] = jsonpath_allow_lists
        return self.send_redact_request("/api/redact/json", payload, random_seed)

    def redact_xml(
        self,
        xml_data: str,
        generator_default: Union[PiiState, str] = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
    ) -> RedactionResponse:
        """Redacts the values in an XML blob. Depending on the configured handling for
        each entity type, values are either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        xml_data : str
            The XML for which to redact values.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for the entity type matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        RedactionResponse
            The redacted string plus additional information.
        """

        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)

        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            label_allow_lists,
            None,
            custom_entities
        )
        payload["xmlText"] = xml_data        

        return self.send_redact_request("/api/redact/xml", payload, random_seed)

    def redact_html(
        self,
        html_data: str,
        generator_default: Union[PiiState, str] = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        custom_entities: Optional[List[str]] = None,
        record_options: RecordApiRequestOptions = default_record_options,
    ) -> RedactionResponse:
        """Redacts the values in an HTML blob. Depending on the configured handling for
        each entity type, values are either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        html_data : str
            The HTML for which to redact values.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). The ignored values are regular expressions. When a value for the entity type matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). The additional values are regular expressions. When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        record_options: RecordApiRequestOptions
            A value to record the API request and results for analysis in the
            Textual application. The default value is to not record the API
            request.  Must specify a time between 1 and 720 hours (inclusive).
            
        Returns
        -------
        RedactionResponse
            The redacted string plus additional information.
        """

        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)

        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            label_allow_lists,
            record_options,
            custom_entities
        )
        payload["htmlText"] = html_data        

        return self.send_redact_request("/api/redact/html", payload, random_seed)

    def send_redact_request(
        self,
        endpoint: str,
        payload: Dict,
        random_seed: Optional[int] = None,
    ) -> RedactionResponse:
        """Helper function to send redact requests, handle responses, and catch errors."""

        if random_seed is not None:
            additional_headers = {"textual-random-seed": str(random_seed)}
        else:
            additional_headers = {}

        try:
            
            response = self.client.http_post(
                endpoint,
                data=payload,
                additional_headers=additional_headers
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise InvalidJsonForRedactionRequest(e.response.text)
            raise e

        de_id_results = [
            Replacement(
                start=result["start"],
                end=result["end"],
                new_start=result.get("newStart"),
                new_end=result.get("newEnd"),
                label=result["label"],
                text=result["text"],
                new_text=result.get("newText"),
                score=result["score"],
                language=result.get("language"),
                example_redaction=result.get("exampleRedaction"),
                json_path=result.get("jsonPath"),
                xml_path=result.get("xmlPath"),
            )
            for result in response["deIdentifyResults"]
        ]

        return RedactionResponse(
            response["originalText"],
            response["redactedText"],
            response["usage"],
            de_id_results,
        )

    def send_redact_bulk_request(
        self,
        endpoint: str,
        payload: Dict,
        random_seed: Optional[int] = None,
    ) -> BulkRedactionResponse:
        """Helper function to send redact requests, handle responses, and catch errors."""

        if random_seed is not None:
            additional_headers = {"textual-random-seed": str(random_seed)}
        else:
            additional_headers = {}

        try:
            response = self.client.http_post(
                endpoint, data=payload, additional_headers=additional_headers
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise InvalidJsonForRedactionRequest(e.response.text)
            raise e

        de_id_results = [[] for i in range(len(response["bulkText"]))]
        for result in response["deIdentifyResults"]:
            de_id_results[result["idx"]].append(
                Replacement(
                    start=result["start"],
                    end=result["end"],
                    new_start=result.get("newStart"),
                    new_end=result.get("newEnd"),
                    label=result["label"],
                    text=result["text"],
                    new_text=result.get("newText"),
                    score=result["score"],
                    language=result.get("language"),
                    example_redaction=result.get("exampleRedaction"),
                )
            )

        return BulkRedactionResponse(
            response["bulkText"],
            response["bulkRedactedText"],
            response["usage"],
            de_id_results,
        )

    def start_file_redaction(
        self,
        file: io.IOBase,
        file_name: str,
        custom_entities: Optional[List[str]] = None,
    ) -> str:
        """
        Redact a provided file

        Parameters
        --------
        file: io.IOBase
            The opened file, available for reading, to upload and redact.
        file_name: str
            The name of the file.
        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        str
           The job identifier, which can be used to download the redacted file when it is ready.

        """

        files = {
            "document": (
                None,
                json.dumps(
                    {
                        "fileName": file_name,
                        "csvConfig": {},
                        "datasetId": "",
                        "customPiiEntityIds": custom_entities
                        if custom_entities
                        else [],
                    }
                ),
                "application/json",
            ),
            "file": file,
        }

        response = self.client.http_post("/api/unattachedfile/upload", files=files)

        return response["jobId"]

    def download_redacted_file(
        self,
        job_id: str,
        generator_default: Union[PiiState, str] = PiiState.Redaction,
        generator_config: Dict[str, Union[PiiState, str]] = dict(),
        generator_metadata: Dict[str, BaseMetadata] = dict(),
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        num_retries: int = 6,
        wait_between_retries: int = 10,
        custom_entities: Optional[List[str]] = None,
    ) -> bytes:
        """
        Download a redacted file

        Parameters
        --------
        job_id: str
            The identifier of the redaction job.

        generator_default: Union[PiiState, str] = PiiState.Redaction
            The default redaction used for types that are not specified in
            generator_config. Value must be one of "Redaction", "Synthesis", or
            "Off".

        generator_config: Dict[str, Union[PiiState, str]]
            A dictionary of sensitive data entities. For each entity, indicates
            whether to redact, synthesize, or ignore it. Values must be one of
            "Redaction", "Synthesis", or "Off".

        generator_metadata: Dict[str, BaseMetadata]
            A dictionary of sensitive data entities. For each entity, indicates
            generator configuration in case synthesis is selected.  Values must
            be of types appropriate to the PII type.v

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random
            number seeding. Can be used to ensure that different API calls use
            the same or different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for the
            entity type matches a listed regular expression, the value is
            ignored and is not redacted or synthesized.

        num_retries: int = 6
            An optional value to specify the number of times to attempt to
            download the file. If a file is not yet ready for download, Textual
            pauses for 10 seconds before retrying. (The default value is 6)

        wait_between_retries: int = 10
            The number of seconds to wait between retry attempts. (The default
            value is 10)

        custom_entities: Optional[List[str]]
            A list of custom entity type identifiers to include. Each custom
            entity type included here may also be included in the generator
            config. Custom entity types will respect generator defaults if they
            are not specified in the generator config.

        Returns
        -------
        bytes
            The redacted file as a byte array.
        """

        validate_generator_default_and_config(generator_default, generator_config, custom_entities)

        validate_generator_metadata(generator_metadata, custom_entities)

        if random_seed is not None:
            additional_headers = {"textual-random-seed": str(random_seed)}
        else:
            additional_headers = {}
        
        payload = generate_redact_payload(
            generator_default,
            generator_config,
            generator_metadata,
            label_block_lists,
            None,
            None,
            custom_entities
        )        

        retries = 1
        while retries <= num_retries:
            try:                
                return self.client.http_post_download_file(
                    f"/api/unattachedfile/{job_id}/download",
                    data=payload,
                    additional_headers=additional_headers,
                )

            except FileNotReadyForDownload:
                retries = retries + 1
                if retries <= num_retries:
                    sleep(wait_between_retries)

        retryWord = "retry" if num_retries == 1 else "retries"
        raise FileNotReadyForDownload(
            f"After {num_retries} {retryWord}, the file is not yet ready to download. "
            "This is likely due to a high service load. Try again later."
        )

class TonicTextual(TextualNer):
    pass
