import math
from time import sleep
from typing import Dict, List, Optional, Union

import requests

from tonic_textual.classes.common_api_responses.label_custom_list import (
    LabelCustomList,
)
from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_api_model import (
    NerRedactionApiModel,
)
from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_page_api_model import (
    NerRedactionPageApiModel,
)
from tonic_textual.classes.common_api_responses.pii_occurences.paginated_pii_occurrence_response import (
    PaginatedPiiOccurrenceResponse,
)
from tonic_textual.classes.common_api_responses.pii_occurences.pii_occurrence_response import (
    PiiOccurrenceResponse,
)
from tonic_textual.classes.enums.file_redaction_policies import (
    docx_comment_policy,
    docx_image_policy,
    docx_table_policy,
    pdf_signature_policy,
    pdf_synth_mode_policy,
)
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.tonic_exception import FileNotReadyForDownload
from tonic_textual.enums.pii_type import PiiType


class DatasetFile:
    """
    Class to store the metadata for a dataset file.

    Parameters
    ----------
    id : str
        The identifier of the dataset file.

    name: str
        The file name of the dataset file.

    num_rows : long
        The number of rows in the dataset file.

    num_columns: int
        The number of columns in the dataset file.

    processing_status: string
        The status of the dataset file in the processing pipeline. Possible values are
        'Completed', 'Failed', 'Cancelled', 'Running', and 'Queued'.

    processing_error: string
        If the dataset file processing failed, a description of the issue that caused
        the failure.

    label_allow_lists: Dict[str, LabelCustomList]
        A dictionary of custom entity detection regular expressions for the dataset file. Each key is an entity type to detect,
        and each values is a LabelCustomList object, whose regular expressions should be recognized as the specified entity type.

    docx_image_policy_name: Optional[docx_image_policy] = None
        The policy for handling images in DOCX files. Options are 'redact', 'ignore', and 'remove'.
    
    docx_comment_policy_name: Optional[docx_comment_policy] = None
        The policy for handling comments in DOCX files. Options are 'remove' and 'ignore'.
    
    docx_table_policy_name: Optional[docx_table_policy] = None
        The policy for handling tables in DOCX files. Options are 'redact' and 'remove'.
    
    pdf_signature_policy_name: Optional[pdf_signature_policy] = None
        The policy for handling signatures in PDF files. Options are 'redact' and 'ignore'.
    
    pdf_synth_mode_policy: Optional[pdf_synth_mode_policy] = None
        The policy for which version of PDF synthesis to use.  Options are V1 and V2.
    """

    _TRANSIENT_DOWNLOAD_STATUS_CODES = frozenset({429, 502, 503, 504})
    _MAX_RETRY_DELAY_SECONDS = 60

    def __init__(
        self,
        client: HttpClient,
        id: str,
        dataset_id: str,
        name: str,
        num_rows: Optional[int],
        num_columns: int,
        processing_status: str,
        processing_error: Optional[str],
        label_allow_lists: Optional[Dict[str, LabelCustomList]] = None,
        docx_image_policy_name: Optional[docx_image_policy] = docx_image_policy.redact,
        docx_comment_policy_name: Optional[
            docx_comment_policy
        ] = docx_comment_policy.remove,
        docx_table_policy_name: Optional[
            docx_table_policy
        ] = docx_table_policy.redact,
        pdf_signature_policy_name: Optional[
            pdf_signature_policy
        ] = pdf_signature_policy.redact,
        pdf_synth_mode_policy: Optional[
            pdf_synth_mode_policy
        ] = pdf_synth_mode_policy.V1
    ):
        self.client = client
        self.id = id
        self.dataset_id = dataset_id
        self.name = name
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.processing_status = processing_status
        self.processing_error = processing_error
        self.label_allow_lists = label_allow_lists
        self.docx_image_policy = docx_image_policy_name
        self.docx_comment_policy = docx_comment_policy_name
        self.docx_table_policy = docx_table_policy_name
        self.pdf_signature_policy = pdf_signature_policy_name
        self.pdf_synth_mode_policy = pdf_synth_mode_policy

        self._pii_occurence_file_limit = 1000

    def describe(self) -> str:
        """Returns the dataset file metadata as string. Includes the identifier, file
        name, number of rows, and number of columns."""
        description = f"File: {self.name} [{self.id}]\n"
        description += f"Number of rows: {self.num_rows}\n"
        description += f"Number of columns: {self.num_columns}\n"
        description += f"Status: {self.processing_status}\n"
        if self.processing_status != "" and self.processing_error is not None:
            description += f"Error: {self.processing_error}\n"
        return description

    def download(
        self,
        random_seed: Optional[int] = None,
        num_retries: int = 6,
        wait_between_retries: int = 10,
    ) -> bytes:
        """
        Download a redacted file

        Parameters
        --------
        random_seed: Optional[int] = None
            An optional value to use to override Textual's default random number
            seeding. Can be used to ensure that different API calls use the same or
            different random seeds.

        num_retries: int = 6
            An optional value to specify the number of times to attempt to download the
            file. Files that are not ready and transient HTTP failures (429, 502, 503,
            and 504) are retried. (The default value is 6)

        wait_between_retries: int = 10
            The fixed number of seconds to wait when a file is not ready. Transient
            HTTP failures use this value as the initial exponential-backoff delay.

        Returns
        -------
        bytes
            The redacted file as a byte array.
        """
        if num_retries < 1:
            raise ValueError("num_retries must be at least 1")

        last_error = None
        for attempt in range(1, num_retries + 1):
            retry_delay = max(wait_between_retries, 0)
            try:
                if random_seed is not None:
                    additional_headers = {"textual-random-seed": str(random_seed)}
                else:
                    additional_headers = {}
                with requests.Session() as session:
                    return self.client.http_get_file(
                        f"/api/dataset/{self.dataset_id}/files/{self.id}/download",
                        additional_headers=additional_headers,
                        session=session,
                    )

            except FileNotReadyForDownload as error:
                last_error = error
            except requests.exceptions.HTTPError as error:
                if not self._is_transient_download_error(error):
                    raise
                last_error = error
                retry_delay = self._transient_retry_delay(
                    error,
                    attempt,
                    wait_between_retries,
                )

            if attempt < num_retries:
                sleep(retry_delay)

        if isinstance(last_error, requests.exceptions.HTTPError):
            raise last_error

        retry_word = "retry" if num_retries == 1 else "retries"
        raise FileNotReadyForDownload(
            f"After {num_retries} {retry_word}, the file is not yet ready to download. "
            "This is likely due to a high service load. Try again later."
        )

    # Report whether an HTTP failure is safe to retry without changing the request.
    @classmethod
    def _is_transient_download_error(cls, error: requests.exceptions.HTTPError) -> bool:
        return (
            error.response is not None
            and error.response.status_code in cls._TRANSIENT_DOWNLOAD_STATUS_CODES
        )

    # Compute bounded exponential backoff while honoring a safe numeric Retry-After header.
    @classmethod
    def _transient_retry_delay(
        cls,
        error: requests.exceptions.HTTPError,
        attempt: int,
        wait_between_retries: int,
    ) -> float:
        backoff = min(
            max(wait_between_retries, 0) * (2 ** (attempt - 1)),
            cls._MAX_RETRY_DELAY_SECONDS,
        )
        response = error.response
        if response is None:
            return backoff

        retry_after = response.headers.get("Retry-After")
        try:
            retry_after_seconds = float(retry_after)
        except (TypeError, ValueError):
            return backoff

        if not math.isfinite(retry_after_seconds) or retry_after_seconds < 0:
            return backoff

        return min(
            max(backoff, retry_after_seconds),
            cls._MAX_RETRY_DELAY_SECONDS,
        )


    def get_entities(self, pii_types: Optional[List[Union[PiiType, str]]] = None) -> Dict[PiiType, List[NerRedactionApiModel]]:        
        
        types_to_find = [p.value if isinstance(p,PiiType) else p for p in pii_types] if pii_types is not None else [p.value for p in PiiType]
        response = dict()
        for pii_type in types_to_find:
            response[pii_type] = self.__get_occurences(pii_type)
        
        return response
    
    def __get_occurences(self, pii_type: PiiType) -> List[NerRedactionApiModel]:
        
        offset = 0      
        pagination = {'fileOffset': offset, 'fileLimit': self._pii_occurence_file_limit, 'datasetFileId': self.id}
        
        occurences: List[NerRedactionApiModel] = []
        with requests.Session() as session:
            while True:
                response = self.client.http_get(f"/api/dataset/{self.dataset_id}/pii_occurrences/{pii_type}", session=session, params=pagination)

                records: List[PiiOccurrenceResponse] = []
                for record in response["records"]:
                    id = record["id"]
                    file_name = record["fileName"]

                    pages: List[NerRedactionPageApiModel] = []
                    for page in record["pages"]:
                        page_number = page["pageNumber"]
                        continuation_token = page["continuationToken"]

                        entities: List[NerRedactionApiModel] = []
                        for entity in page["entities"]:
                            entities.append(NerRedactionApiModel(entity["entity"], entity["head"], entity["tail"]))
                        
                        pages.append(NerRedactionPageApiModel(page_number, entities, continuation_token))
                    records.append(PiiOccurrenceResponse(id, file_name, pages))
                
                paginated_response = PaginatedPiiOccurrenceResponse(response["offset"], response["limit"], response["pageNumber"], response["totalPages"], response["totalRecords"], response["hasNextPage"], records)                

                for record in paginated_response.records:
                    for page in record.pages:
                        occurences = occurences + page.entities
                
                if len(pages)>0:
                    last_page = pages[-1]
                    if last_page.continuation_token is not None:
                        pagination["fileOffset"] = last_page.continuation_token
                    else:
                        break
                else:
                    break                

        return occurences
