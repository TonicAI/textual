import requests
from time import sleep
from typing import Optional, Dict, List, Union

from tonic_textual.classes.common_api_responses.label_custom_list import LabelCustomList
from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_api_model import NerRedactionApiModel
from tonic_textual.classes.common_api_responses.pii_occurences.ner_redaction_page_api_model import NerRedactionPageApiModel
from tonic_textual.classes.common_api_responses.pii_occurences.paginated_pii_occurrence_response import PaginatedPiiOccurrenceResponse
from tonic_textual.classes.common_api_responses.pii_occurences.pii_occurrence_response import PiiOccurrenceResponse
from tonic_textual.classes.enums.file_redaction_policies import (
    docx_image_policy,
    docx_comment_policy,
    pdf_signature_policy,
    docx_table_policy,
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
            file. If a file is not yet ready for download, there is a 10-second
            pause before retrying. (The default value is 6)

        wait_between_retries: int = 10
            The number of seconds to wait between retry attempts.

        Returns
        -------
        bytes
            The redacted file as a byte array.
        """
        retries = 1
        while retries <= num_retries:
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

            except FileNotReadyForDownload:
                retries = retries + 1
                if retries <= num_retries:
                    sleep(wait_between_retries)

        retryWord = "retry" if num_retries == 1 else "retries"
        raise FileNotReadyForDownload(
            f"After {num_retries} {retryWord}, the file is not yet ready to download. "
            "This is likely due to a high service load. Try again later."
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