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
from tonic_textual.classes.tonic_exception import DatasetFileMatchesExistingFile, DatasetFileNotFound, \
    DatasetNameAlreadyExists, BadArgumentsException
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
        Serialized DatasetFile objects representing the files in a dataset.

    client: HttpClient
        The HTTP client to use.
    """

    def __init__(
            self, client: HttpClient, id: str, name: str, files: List[Dict[str, Any]],
            generator_config: Optional[Dict[str, PiiState]] = None,
            label_block_lists: Optional[Dict[str, List[str]]] = None,
            label_allow_lists: Optional[Dict[str, List[str]]] = None
    ):
        self.__initialize(client, id, name, files, generator_config, label_block_lists, label_allow_lists)

    def __initialize(self, client: HttpClient, id: str, name: str, files: List[Dict[str, Any]],
                     generator_config: Optional[Dict[str, PiiState]] = None,
                     label_block_lists: Optional[Dict[str, List[str]]] = None,
                     label_allow_lists: Optional[Dict[str, List[str]]] = None):
        self.id = id
        self.name = name
        self.client = client
        self.datasetfile_service = DatasetFileService(self.client)
        self.generator_config = generator_config
        self.label_block_lists = label_block_lists
        self.label_allow_lists = label_allow_lists
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
                f.get("labelAllowLists")
        )
            for f in files
        ]

        if len(self.files) > 0:
            self.num_columns = max([f.num_columns for f in self.files])
        else:
            self.num_columns = None

    def edit(self, name: Optional[str] = None, generator_config: Optional[Dict[str, PiiState]] = None,
             label_block_lists: Optional[Dict[str, List[str]]] = None,
             label_allow_lists: Optional[Dict[str, List[str]]] = None,
             should_rescan = True):
        """
        Edit dataset.  Only fields provided as function arguments will be edited.  Currently, supports editing the name of the dataset and the generator setup (how each entity is handled during redaction/synthesis)

        Parameters
        --------
        name: Optional[str]
            The new name of the dataset.  Will return an error if the new name conflicts with an existing dataset name
        generator_config: Optional[Dict[str, PiiState]]
            A dictionary of sensitive data entities. For each entity, indicates whether
            to redact, synthesize, or ignore it.
        label_block_lists: Optional[Dict[str, List[str]]]
            A dictionary of (pii type, ignored entities). When an entity of pii type, matching a regex in the list, is found,
            the value will be ignored and not redacted or synthesized.
        label_allow_lists: Optional[Dict[str, List[str]]]
            A dictionary of (pii type, included entities). When a piece of text matches a regex in the list,
            said text will be marked as the pii type and be included in redaction or synthesis.

        Raises
        ------

        DatasetNameAlreadyExists
            Raised if a dataset with the same name already exists.

        """
        if generator_config is not None:
            validate_generator_options(PiiState.Off, generator_config)

        data = {
            'id': self.id,
            'name': name if name is not None and len(name) > 0 else self.name,
            'generatorSetup': generator_config,
        }
        if label_block_lists is not None:
            data['labelBlockLists'] = {k: LabelCustomList(regexes=v).to_dict() for k, v in label_block_lists.items()}
        if label_allow_lists is not None:
            data['labelAllowLists'] = {k: LabelCustomList(regexes=v).to_dict() for k, v in label_allow_lists.items()}

        try:
            new_dataset = self.client.http_put(f'/api/dataset?shouldRescan={str(should_rescan)}', data=data)
            self.__initialize(self.client, new_dataset['id'], new_dataset['name'], new_dataset['files'],
                              new_dataset['generatorSetup'], new_dataset['labelBlockLists'],
                              new_dataset['labelAllowLists'])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise DatasetNameAlreadyExists(e)

    def add_file(self, file_path: Optional[str] = None, file_name: Optional[str] = None,
                 file: Optional[io.IOBase] = None, ) -> Optional[DatasetFile]:
        """
        Uploads a file to the dataset.

        Parameters
        --------
        file_path: Optional[str]
            The absolute path of the file to upload.  If specified you cannot also provide the 'file' argument.
        file_name: Optional[str]
            The name of the file to save to Tonic Textual.  This is optional if uploading a file via file_path but required if using the 'file' argument
        file: Optional[io.IOBase]
            The bytes of a file to be uploaded.  If specified you must also provide the 'file_name' argument.  The 'file_path' argument cannot be used in the same call.
        Raises
        ------

        DatasetFileMatchesExistingFile
            Returned if the file content matches an existing file.

        """

        if file_path is not None and file is not None:
            raise BadArgumentsException("You must only specify a file path or a file, not both")

        if file is not None and file_name is None:
            raise BadArgumentsException("When passing in a file you must specify the file_name parameter as well")

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

        updated_dataset = uploaded_file_response_model.get('updatedDataset')
        uploaded_file_id = uploaded_file_response_model.get('uploadedFileId')

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
                f.get("labelAllowLists")
            )
            for f in updated_dataset["files"]
        ]
        self.num_columns = max([f.num_columns for f in self.files])

        matched_files = list(filter(lambda x: x.id==uploaded_file_id, self.files))
        return matched_files[0]


    def delete_file(self, file_id: str):
        """
        Deletes the given file from the dataset

        Parameters
        --------
        file_id: str
            The ID of the file in the dataset to delete
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
                "Pandas is required to fetch the dataset data as a pandas dataframe. Please install pandas before using this method."
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
            The datset data.
        """
        response = []
        with requests.Session() as session:
            for file in self.files:
                try:
                    if file.num_columns == 0:
                        more_data = self.client.http_get_file(
                            f"/api/dataset/{self.id}/files/{file.id}/get_data",
                            session=session,
                        ).decode('utf-8')
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
        Gets all of the files in the dataset for which processing is complete. The data
        in these files is returned when data is requested.

        Returns
        ------
        List[DatasetFile]:
            The list of processed dataset files.
        """
        return list(filter(lambda x: x.processing_status == "Completed", self.files))

    def get_queued_files(self) -> List[DatasetFile]:
        """
        Gets all of the files in the dataset that are waiting to be processed.

        Returns
        ------
        List[DatasetFile]:
            The list of dataset files that await processing.
        """
        return list(filter(lambda x: x.processing_status == "Queued", self.files))

    def get_running_files(self) -> List[DatasetFile]:
        """
        Gets all of the files in the dataset that are currently being processed.

        Returns
        ------
        List[DatasetFile]:
            The list of files that are being processed.
        """
        return list(filter(lambda x: x.processing_status == "Running", self.files))

    def get_failed_files(self) -> List[DatasetFile]:
        """
        Gets all of the files in dataset that encountered an error when they were
        processed. These files are effectively ignored.

        Returns
        ------
        List[DatasetFile]:
            The list of files that had processing errors.
        """
        return list(filter(lambda x: x.processing_status == "Failed", self.files))

    def _check_processing_and_update(self):
        """
        Checks the processing status of the files in the dataset and updates the files
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
        result += f"{', '.join([str((f.id, f.name)) for f in files_waiting_for_proc])}\n"
        result += "Files that encountered errors while processing: "
        result += f"{', '.join([str((f.id, f.name)) for f in files_with_error])}\n"
        return result
