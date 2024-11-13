import io
import json
import os
import requests

from time import sleep
from typing import List, Optional, Union, Dict
from urllib.parse import urlencode

from tonic_textual.classes.common_api_responses.label_custom_list import LabelCustomList
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.common_api_responses.single_detection_result import (
    SingleDetectionResult,
)
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.services.dataset import DatasetService
from tonic_textual.services.datasetfile import DatasetFileService
from tonic_textual.classes.dataset import Dataset
from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.classes.tonic_exception import (
    DatasetNameAlreadyExists,
    InvalidJsonForRedactionRequest,
    FileNotReadyForDownload,
)

from tonic_textual.generator_utils import validate_generator_options


class TextualNer:
    """Wrapper class for invoking Tonic Textual API

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes.
    api_key : str
        Your API token. This argument is optional. Instead of providing the API token
        here, it is recommended that you set the API key in your environment as the
        value of TONIC_TEXTUAL_API_KEY.
    verify: bool
        Whether SSL Certification verification is performed.  This is enabled by
        default.
    Examples
    --------
    >>> from tonic_textual.redact_api import TextualNer
    >>> textual = TonicTextual("https://textual.tonic.ai")
    """

    def __init__(
        self, base_url: str, api_key: Optional[str] = None, verify: bool = True
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
            An optional value to use to override Textual's default random number
            seeding.  Can be used to ensure that different API calls use the same or
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
            seeding.  Can be used to ensure that different API calls use the same or
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

    def redact(
        self,
        string: str,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
    ) -> RedactionResponse:
        """Redacts a string. Depending on the configured handling for each sensitive
        data type, values can be either redacted, synthesized, or ignored.

        Parameters
        ----------
        string : str
            The string to redact.

        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates whether
            to redact, synthesize, or ignore it.
            Values must be one of "Redaction", "Synthesis", or "Off".

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for all types not specified in generator_config.
            Values must be one of "Redaction", "Synthesis", or "Off".

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for an entity type matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.


        Returns
        -------
        RedactionResponse
            The redacted string along with ancillary information.

        Examples
        --------
            >>> textual.redact(
            >>>     "John Smith is a person",
            >>>     # only redacts NAME_GIVEN
            >>>     generator_config={"NAME_GIVEN": "Redaction"},
            >>>     generator_default="Off",
            >>>     # Occurrences of "There" are treated as NAME_GIVEN entities
            >>>     label_allow_lists={"NAME_GIVEN": ["There"]},
            >>>     # Text matching the regex ` ([a-z]{2}) ` is not treated as an occurrence of NAME_FAMILY
            >>>     label_block_lists={"NAME_FAMILY": [" ([a-z]{2}) "]},
            >>> )


        """

        validate_generator_options(generator_default, generator_config)
        payload = {
            "text": string,
            "generatorDefault": generator_default,
            "generatorConfig": generator_config,
        }

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

        return self.send_redact_request("/api/redact", payload, random_seed)

    def llm_synthesis(
        self,
        string: str,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
    ) -> RedactionResponse:
        """Deidentifies a string by redacting sensitive data and replacing these values
        with values generated by an LLM.

        Parameters
        ----------
        string: str
                The string to redact.

        generator_config: Dict[str, PiiState]
                A dictionary of sensitive data entities. For each entity, indicates
                whether to redact, synthesize, or ignore it.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for all types not specified in generator_config.

        Returns
        -------
        RedactionResponse
            The redacted string, along with ancillary information about the detected entities.
        """
        validate_generator_options(generator_default, generator_config)
        endpoint = "/api/synthesis"
        response = self.client.http_post(
            endpoint,
            data={
                "text": string,
                "generatorDefault": generator_default,
                "generatorConfig": generator_config,
            },
        )

        de_id_results = [
            SingleDetectionResult(
                x["start"], x["end"], x["label"], x["text"], x["score"]
            )
            for x in list(response["deIdentifyResults"])
        ]

        return RedactionResponse(
            response["originalText"],
            response["redactedText"],
            response["usage"],
            de_id_results,
        )

    def redact_json(
        self,
        json_data: Union[str, dict],
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        jsonpath_allow_lists: Optional[Dict[str, List[str]]] = None,
    ) -> RedactionResponse:
        """Redacts the values in a JSON blob. Depending on the configured handling for
        each sensitive data type, values can be either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        json_string : Union[str, dict]
            The JSON whose values will be redacted.  This can be either a JSON string
            or a Python dictionary

        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates whether
            to redact, synthesize, or ignore it.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for all types not specified in generator_config.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When an value for the entity type, matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.

        jsonpath_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, path expression). When an element in the JSON document matches the JSON path expression, the entire text value is treated as the specified entity type.
            Only supported for path expressions that point to JSON primitive values. This setting overrides any results found by the NER model or in label allow and block lists.
            If multiple path expressions point to the same JSON node, but specify different entity types, then the value is redacted as one of those types. However, the chosen type is selected at random - it could use any of the types.

        Returns
        -------
        RedactionResponse
            The redacted string along with ancillary information.
        """
        validate_generator_options(generator_default, generator_config)

        if isinstance(json_data, str):
            json_text = json_data
        elif isinstance(json_data, dict):
            json_text = json.dumps(json_data)
        else:
            raise Exception(
                "redact_json must receive either a JSON blob as a string or dict(). "
                f"You passed in type {type(json_data)} which is not supported"
            )
        payload = {
            "jsonText": json_text,
            "generatorDefault": generator_default,
            "generatorConfig": generator_config,
        }
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
        if jsonpath_allow_lists is not None:
            payload["jsonPathAllowLists"] = jsonpath_allow_lists
        return self.send_redact_request("/api/redact/json", payload, random_seed)

    def redact_xml(
        self,
        xml_data: str,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
    ) -> RedactionResponse:
        """Redacts the values in an XML blob. Depending on the configured handling for
        each entity type, values are either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        xml_data : str
            The XML for which to redact values.

        generator_config: Dict[str, PiiState]
            A dictionary of entity types. For each entity type, indicates
            whether to redact, synthesize, or ignore the detected values.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for any entity type that is not included in generator_config.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When an value for the entity type, matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, additional values). When a piece of text matches a listed regular expression,
            the text is marked as the entity type and is included in the redaction or synthesis.

        Returns
        -------
        RedactionResponse
            The redacted string plus additional information.
        """
        validate_generator_options(generator_default, generator_config)

        payload = {
            "xmlText": xml_data,
            "generatorDefault": generator_default,
            "generatorConfig": generator_config,
        }

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

        return self.send_redact_request("/api/redact/xml", payload, random_seed)

    def redact_html(
        self,
        html_data: str,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
    ) -> RedactionResponse:
        """Redacts the values in an HTML blob. Depending on the configured handling for
        each entity type, values are either redacted, synthesized, or
        ignored.

        Parameters
        ----------
        html_data : str
            The HTML for which to redact values.

        generator_config: Dict[str, PiiState]
            A dictionary of entity types. For each entity type, indicates
            whether to redact, synthesize, or ignore the detected values.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for any entity type that is not included in generator_config.

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

        Returns
        -------
        RedactionResponse
            The redacted string plus additional information.
        """
        validate_generator_options(generator_default, generator_config)

        payload = {
            "htmlText": html_data,
            "generatorDefault": generator_default,
            "generatorConfig": generator_config,
        }

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
                endpoint, data=payload, additional_headers=additional_headers
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                raise InvalidJsonForRedactionRequest(e.response.text)
            raise e

        de_id_results = [
            Replacement(
                start=x["start"],
                end=x["end"],
                new_start=x.get("newStart"),
                new_end=x.get("newEnd"),
                label=x["label"],
                text=x["text"],
                new_text=x.get("newText"),
                score=x["score"],
                language=x.get("language"),
                example_redaction=x.get("exampleRedaction"),
                json_path=x.get("jsonPath"),
                xml_path=x.get("xmlPath"),
            )
            for x in response["deIdentifyResults"]
        ]

        return RedactionResponse(
            response["originalText"],
            response["redactedText"],
            response["usage"],
            de_id_results,
        )

    def start_file_redaction(self, file: io.IOBase, file_name: str) -> str:
        """
        Redact a provided file

        Parameters
        --------
        file: io.IOBase
            The opened file, available for reading, which will be uploaded and redacted
        file_name: str
            The name of the file

        Returns
        -------
        str
           The job id which can be used to download the redacted file once it is ready

        """

        files = {
            "document": (
                None,
                json.dumps({"fileName": file_name, "csvConfig": {}, "datasetId": ""}),
                "application/json",
            ),
            "file": file,
        }

        response = self.client.http_post("/api/unattachedfile/upload", files=files)

        return response["jobId"]

    def download_redacted_file(
        self,
        job_id: str,
        generator_config: Dict[str, PiiState] = dict(),
        generator_default: PiiState = PiiState.Redaction,
        random_seed: Optional[int] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        num_retries: int = 6,
        wait_between_retries: int = 10,
    ) -> bytes:
        """
        Download a redacted file

        Parameters
        --------
        job_id: str
            The ID of the redaction job

        generator_config: Dict[str, PiiState]
            A dictionary of sensitive data entities. For each entity, indicates whether
            to redact, synthesize, or ignore it.

        generator_default: PiiState = PiiState.Redaction
            The default redaction used for all types not specified in generator_config.

        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored values). When a value for the entity type matches a listed regular expression,
            the value is ignored and is not redacted or synthesized.

        num_retries: int = 6
            An optional value to specify how many times to attempt to download the
            file.  If a file is not yet ready for download, there will be a 10 second
            pause before retrying. (The default value is 6)

        wait_between_retries: int = 10
            The number of seconds to wait between retry attempts. (The default value is 6)

        Returns
        -------
        bytes
            The redacted file as byte array
        """

        validate_generator_options(generator_default, generator_config)
        retries = 1
        while retries <= num_retries:
            try:
                if random_seed is not None:
                    additional_headers = {"textual-random-seed": str(random_seed)}
                else:
                    additional_headers = {}
                data = {
                    "generatorDefault": generator_default,
                    "generatorConfig": generator_config,
                }
                if label_block_lists is not None:
                    data["labelBlockLists"] = {
                        k: LabelCustomList(regexes=v).to_dict()
                        for k, v in label_block_lists.items()
                    }
                return self.client.http_post_download_file(
                    f"/api/unattachedfile/{job_id}/download",
                    data=data,
                    additional_headers=additional_headers,
                )

            except FileNotReadyForDownload:
                retries = retries + 1
                if retries <= num_retries:
                    sleep(wait_between_retries)

        retryWord = "retry" if num_retries == 1 else "retries"
        raise FileNotReadyForDownload(
            f"After {num_retries} {retryWord} the file is not yet ready for download. "
            "This is likely due to a high service load. Please try again later."
        )


class TonicTextual(TextualNer):
    pass
