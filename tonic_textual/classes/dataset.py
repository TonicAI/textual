from __future__ import annotations

import io
from typing import List, Dict, Optional, Any
import os
import json
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
import requests.exceptions
import requests

from tonic_textual.classes.common_api_responses.label_custom_list import LabelCustomList
from tonic_textual.classes.pii_info import DatasetPiiInfo
from tonic_textual.classes.enums.file_redaction_policies import docx_image_policy, docx_comment_policy, \
    pdf_signature_policy, docx_table_policy
from tonic_textual.classes.tonic_exception import (
    DatasetFileMatchesExistingFile,
    DatasetFileNotFound,
    DatasetNameAlreadyExists,
    BadArgumentsException,
)
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.generator_utils import validate_generator_options
from tonic_textual.services.datasetfile import DatasetFileService


class Dataset:
    """Class to represent and provide access to a Tonic Textual dataset.

    Parameters
    ----------
    id: str
        Dataset identifier.

    name: str
        Dataset name.

    files: Dict
        Serialized DatasetFile objects that represent the files in a dataset.

    client: HttpClient
        The HTTP client to use.
    """

    def __init__(
        self,
        client: HttpClient,
        id: str,
        name: str,
        files: List[Dict[str, Any]],
        generator_config: Optional[Dict[str, PiiState]] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        docx_image_policy_name: Optional[docx_image_policy] = docx_image_policy.redact,
        docx_comment_policy_name: Optional[docx_comment_policy] = docx_comment_policy.remove,
        docx_table_policy_name: Optional[docx_table_policy] = docx_table_policy.remove,
        pdf_signature_policy_name: Optional[pdf_signature_policy] = pdf_signature_policy.redact
        ):
        self.__initialize(
            client,
            id,
            name,
            files,
            generator_config,
            label_block_lists,
            label_allow_lists,
            docx_image_policy_name,
            docx_comment_policy_name,
            docx_table_policy_name,
            pdf_signature_policy_name
        )

    def __initialize(
        self,
        client: HttpClient,
        id: str,
        name: str,
        files: List[Dict[str, Any]],
        generator_config: Optional[Dict[str, PiiState]] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        docx_image_policy_name: Optional[docx_image_policy] = docx_image_policy.redact,
        docx_comment_policy_name: Optional[docx_comment_policy] = docx_comment_policy.remove,
        docx_table_policy_name: Optional[docx_table_policy] = docx_table_policy.redact,
        pdf_signature_policy_name: Optional[pdf_signature_policy] = pdf_signature_policy.redact
    ):
        self.id = id
        self.name = name
        self.client = client
        self.datasetfile_service = DatasetFileService(self.client)
        self.generator_config = generator_config
        self.label_block_lists = label_block_lists
        self.label_allow_lists = label_allow_lists
        self.docx_image_policy = docx_image_policy_name
        self.docx_comment_policy =  docx_comment_policy_name
        self.docx_table_policy = docx_table_policy_name
        self.pdf_signature_policy = pdf_signature_policy_name
        self.files = [
            DatasetFile(
                self.client,
                f["fileId"],
                self.id,
                f["fileName"],
                f.get("numRows"),
                f["numColumns"],
                f["processingStatus"],
                f.get("processingError"),
                f.get("labelAllowLists"),
                f.get("docxImagePolicy"),
                f.get("docxCommentPolicy"),
                f.get("docxTablePolicy"),
                f.get("pdfSignaturePolicy")
            )
            for f in files
        ]

        if len(self.files) > 0:
            self.num_columns = max([f.num_columns for f in self.files])
        else:
            self.num_columns = None
        self._pii_info = None

    @property
    def pii_info(self):
        if self._pii_info is None:
            with requests.Session() as session:
                data = self.client.http_get(f"/api/dataset/{self.id}/pii_info", session=session)
                self._pii_info = DatasetPiiInfo(data, self.files)
        return self._pii_info

    def edit(
        self,
        name: Optional[str] = None,
        generator_config: Optional[Dict[str, PiiState]] = None,
        label_block_lists: Optional[Dict[str, List[str]]] = None,
        label_allow_lists: Optional[Dict[str, List[str]]] = None,
        docx_image_policy_name: Optional[docx_image_policy] = None,
        docx_comment_policy_name: Optional[docx_comment_policy] = None,
        docx_table_policy_name: Optional[docx_table_policy] = None,
        pdf_signature_policy_name: Optional[pdf_signature_policy] = None,
        should_rescan=True,
        copy_from_dataset: Optional[Dataset] = None,
    ):
        """
        Edit dataset. Only edits fields that are provided as function arguments. Currently, you can edit the name of the dataset and the generator setup, which indicate how to handle each entity.

        Parameters
        --------
        name: Optional[str]
            The new name of the dataset. Returns an error if the new name conflicts with an existing dataset name.
        generator_config: Optional[Dict[str, PiiState]]
            A dictionary of sensitive data entities. For each entity, indicates whether
            to redact, synthesize, or ignore it.
        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, ignored entities). When an entity of the specified type matches a regular expression in the list,
            the value is ignored and not redacted or synthesized.
        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (entity type, included entities). When a piece of text matches a regular expression in the list,
            the text is marked as the entity type and is included in the redaction or synthesis.
        docx_image_policy_name: Optional[docx_image_policy] = None
            The policy for handling images in DOCX files. Options are 'redact', 'ignore', and 'remove'.
        docx_comment_policy_name: Optional[docx_comment_policy] = None
            The policy for handling comments in DOCX files. Options are 'remove' and 'ignore'.
        docx_table_policy_name: Optional[docx_table_policy] = None
            The policy for handling tables in DOCX files. Options are 'redact' and 'remove'.
        pdf_signature_policy_name: Optional[pdf_signature_policy] = None
            The policy for handling signatures in PDF files. Options are 'redact' and 'ignore'.
        copy_from_dataset: Optional[Dataset]
            Another dataset object to copy settings from. This parameter is mutually exclusive with the other parameters.

        Raises
        ------

        DatasetNameAlreadyExists
            Raised if a dataset with the same name already exists.
        BadArgumentsException
            Raised if the copy_from_dataset parameter is not None while another parameter is not None.

        """

        if copy_from_dataset is not None and any(param is not None for param in [generator_config, label_block_lists, label_allow_lists, docx_image_policy_name, docx_comment_policy_name, pdf_signature_policy_name]):
            raise BadArgumentsException("The dataset parameter is mutually exclusive with the other parameters.")
        if generator_config is not None:
            validate_generator_options(PiiState.Off, generator_config)

        if copy_from_dataset is not None:
            generator_config = copy_from_dataset.generator_config
            label_block_lists = {pii_type: lbl['regexes'] for pii_type, lbl in copy_from_dataset.label_block_lists.items()}
            label_allow_lists = {pii_type: lbl['regexes'] for pii_type, lbl in copy_from_dataset.label_allow_lists.items()}
            docx_image_policy_name = copy_from_dataset.docx_image_policy
            docx_comment_policy_name = copy_from_dataset.docx_comment_policy
            docx_table_policy_name = copy_from_dataset.docx_table_policy
            pdf_signature_policy_name = copy_from_dataset.pdf_signature_policy

        data = {
            "id": self.id,
            "name": name if name is not None and len(name) > 0 else self.name,
            "generatorSetup": generator_config,
        }
        if label_block_lists is not None:
            data["labelBlockLists"] = {
                k: LabelCustomList(regexes=v).to_dict()
                for k, v in label_block_lists.items()
            }
        if label_allow_lists is not None:
            data["labelAllowLists"] = {
                k: LabelCustomList(regexes=v).to_dict()
                for k, v in label_allow_lists.items()
            }
        if docx_image_policy is not None:
            data["docXImagePolicy"] = docx_image_policy_name
        if docx_comment_policy is not None:
            data["docXCommentPolicy"] = docx_comment_policy_name
        if docx_table_policy is not None:
            data["docXTablePolicy"] = docx_table_policy_name
        if pdf_signature_policy is not None:
            data["pdfSignaturePolicy"] = pdf_signature_policy_name

        try:
            new_dataset = self.client.http_put(
                f"/api/dataset?shouldRescan={str(should_rescan)}", data=data
            )
            self.__initialize(
                self.client,
                new_dataset["id"],
                new_dataset["name"],
                new_dataset["files"],
                new_dataset["generatorSetup"],
                new_dataset["labelBlockLists"],
                new_dataset["labelAllowLists"],
                new_dataset["docXImagePolicy"],
                new_dataset["docXCommentPolicy"],
                new_dataset["docXTablePolicy"],
                new_dataset["pdfSignaturePolicy"]
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise DatasetNameAlreadyExists(e)

    def add_file(
        self,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None,
        file: Optional[io.IOBase] = None,
    ) -> Optional[DatasetFile]:
        """
        Uploads a file to the dataset.

        Parameters
        --------
        file_path: Optional[str]
            The absolute path of the file to upload. If specified, you cannot also provide the 'file' argument.
        file_name: Optional[str]
            The name of the file to save to Tonic Textual. Optional if you use file_path to upload the file. Required if you use the 'file' argument.
        file: Optional[io.IOBase]
            The bytes of a file to upload. If specified, you must also provide the 'file_name' argument. You cannnot use the 'file_path' argument in the same call.
        Raises
        ------

        DatasetFileMatchesExistingFile
            Returned if the file content matches an existing file.

        """

        if file_path is not None and file is not None:
            raise BadArgumentsException(
                "You must only specify a file path or a file. You cannot specify both."
            )

        if file is not None and file_name is None:
            raise BadArgumentsException(
                "When you pass in a file, you must also specify the file_name parameter."
            )

        if file is None and file_path is None:
            raise BadArgumentsException("Must specify either a file_path or file")

        if file_name is None:
            file_name = os.path.basename(file_path)

        f = open(file_path, "rb") if file_path is not None else file

        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)

        with tqdm(
            desc="[INFO] Uploading",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as t:
            reader_wrapper = CallbackIOWrapper(t.update, f, "read")

            files = {
                "document": (
                    None,
                    json.dumps(
                        {
                            "fileName": file_name,
                            "csvConfig": {},
                            "datasetId": self.id,
                        }
                    ),
                    "application/json",
                ),
                "file": reader_wrapper,
            }
            try:
                uploaded_file_response_model = self.client.http_post(
                    f"/api/dataset/{self.id}/files/upload", files=files
                )
                # numRows is null when a file is first uploaded
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:
                    raise DatasetFileMatchesExistingFile(e)
                else:
                    raise e

        if file_path is not None:
            f.close()

        updated_dataset = uploaded_file_response_model.get("updatedDataset")
        uploaded_file_id = uploaded_file_response_model.get("uploadedFileId")

        # to support older version of Tonic Textual when response model was different
        if updated_dataset is None:
            return None

        self.files = [
            DatasetFile(
                self.client,
                f["fileId"],
                self.id,
                f["fileName"],
                f.get("numRows"),
                f["numColumns"],
                f["processingStatus"],
                f.get("processingError"),
                f.get("labelAllowLists"),
                f.get("docxImagePolicy"),
                f.get("docxCommentPolicy"),
                f.get("pdfSignaturePolicy")
            )
            for f in updated_dataset["files"]
        ]
        self.num_columns = max([f.num_columns for f in self.files])

        matched_files = list(filter(lambda x: x.id == uploaded_file_id, self.files))
        return matched_files[0]

    def delete_file(self, file_id: str):
        """
        Deletes the given file from the dataset

        Parameters
        --------
        file_id: str
            The identifier of the dataset file to delete.
        """
        try:
            self.client.http_delete(f"/api/dataset/{self.id}/files/{file_id}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise DatasetFileNotFound(self.name, file_id)
            else:
                raise e

        self.files = list(filter(lambda x: x.id != file_id, self.files))

    def fetch_all_df(self):
        """
        Fetches all of the data in the dataset as a pandas dataframe.

        Returns
        -------
        pd.DataFrame
            Dataset data in a pandas dataframe.
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "Pandas is required to fetch the dataset data as a pandas dataframe. Before you use this method, you must install pandas."
            ) from e
        data = self._fetch_all()

        if self.num_columns is None:
            return pd.DataFrame()

        # RAW file, not CSV
        if self.num_columns == 0:
            if len(data) == 0:
                return pd.DataFrame(columns=["text"])
            return pd.DataFrame(data, columns=["text"])

        columns = ["col" + str(x) for x in range(self.num_columns)]
        if len(data) == 0:
            return pd.DataFrame(columns=columns)
        else:
            return pd.DataFrame(data, columns=columns)

    def fetch_all_json(self) -> str:
        """
        Fetches all of the data in the dataset as JSON.

        Returns
        -------
        str
            Dataset data in JSON format.
        """
        return json.dumps(self._fetch_all())

    def _fetch_all(self) -> List[List[str]]:
        """
        Fetches all data from the dataset.

        Returns
        -------
        List[List[str]]
            The dataset data.
        """
        response = []
        with requests.Session() as session:
            for file in self.files:
                try:
                    if file.num_columns == 0:
                        more_data = self.client.http_get_file(
                            f"/api/dataset/{self.id}/files/{file.id}/get_data",
                            session=session,
                        ).decode("utf-8")
                        response += [[more_data]]
                    else:
                        more_data = self.client.http_get(
                            f"/api/dataset/{self.id}/files/{file.id}/get_data",
                            session=session,
                        )
                        response += more_data
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 409:
                        continue
                    else:
                        raise e
            return response

    def get_processed_files(self) -> List[DatasetFile]:
        """
        Gets all of the dataset files for which processing is complete. The data
        in these files is returned when data is requested.

        Returns
        ------
        List[DatasetFile]:
            The list of processed dataset files.
        """
        return list(filter(lambda x: x.processing_status == "Completed", self.files))

    def get_queued_files(self) -> List[DatasetFile]:
        """
        Gets all of the dataset files that are waiting to be processed.

        Returns
        ------
        List[DatasetFile]:
            The list of dataset files that await processing.
        """
        return list(filter(lambda x: x.processing_status == "Queued", self.files))

    def get_running_files(self) -> List[DatasetFile]:
        """
        Gets all of the dataset files that are currently being processed.

        Returns
        ------
        List[DatasetFile]:
            The list of files that are being processed.
        """
        return list(filter(lambda x: x.processing_status == "Running", self.files))

    def get_failed_files(self) -> List[DatasetFile]:
        """
        Gets all of the dataset files that encountered an error when they were
        processed. These files are effectively ignored.

        Returns
        ------
        List[DatasetFile]:
            The list of files that had processing errors.
        """
        return list(filter(lambda x: x.processing_status == "Failed", self.files))

    def _check_processing_and_update(self):
        """
        Checks the processing status of the files in the dataset. Updates the file
        list.
        """
        if len(self.get_queued_files() + self.get_running_files()) > 0:
            self.files = self.datasetfile_service.get_files(self.id)

    def describe(self) -> str:
        """
        Returns a string of the dataset name, identifier, and the list of files.

        Examples
        --------
        >>> workspace.describe()
        Dataset: your_dataset_name [dataset_id]
        Number of Files: 2
        Number of Rows: 1000
        """
        self._check_processing_and_update()

        files_waiting_for_proc = self.get_queued_files() + self.get_running_files()
        files_with_error = self.get_failed_files()
        result = f"Dataset: {self.name} [{self.id}]\n"
        result += f"Number of Files: {len(self.get_processed_files())}\n"
        result += "Files that are waiting for processing: "
        result += (
            f"{', '.join([str((f.id, f.name)) for f in files_waiting_for_proc])}\n"
        )
        result += "Files that encountered errors while processing: "
        result += f"{', '.join([str((f.id, f.name)) for f in files_with_error])}\n"
        return result
