import io
import json
import os
from typing import List, Optional, Union
from warnings import warn
import requests
from requests import RequestException

from tonic_textual.classes.azure_pipeline import AzurePipeline
from tonic_textual.classes.enums.aws_credentials_source import AwsCredentialsSource
from tonic_textual.classes.enums.file_source import FileSource
from tonic_textual.classes.enums.object_storage_type import ObjectStorageType
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.local_pipeline import LocalPipeline
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult
from tonic_textual.classes.pipeline_aws_credential import PipelineAwsCredential
from tonic_textual.classes.pipeline import Pipeline
from tonic_textual.classes.pipeline_azure_credential import PipelineAzureCredential
from tonic_textual.classes.pipeline_databricks_credential import (
    PipelineDatabricksCredential,
)
from tonic_textual.classes.s3_pipeline import S3Pipeline
from tonic_textual.classes.tonic_exception import (
    BadArgumentsException,
    PipelineDeleteError,
    PipelineCreateError,
)


class TextualParse:
    """Wrapper class for invoking Tonic Textual API

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes.
    api_key : str
        Your API token. This argument is optional. Instead of providing the API token
        here, it is recommended that you set the API key in your environment as the
        value of TEXTUAL_API_KEY.
    verify: bool
        Whether SSL Certification verification is performed.  This is enabled by
        default.
    Examples
    --------
    >>> from tonic_textual.parse_api import TextualParse
    >>> textual = TonicTextualParse("https://textual.tonic.ai")
    """

    def __init__(
        self, base_url: str, api_key: Optional[str] = None, verify: bool = True
    ):
        if api_key is None:
            api_key = os.environ.get("TONIC_TEXTUAL_API_KEY")
            if api_key is None:
                raise Exception(
                    "No API key provided. Either provide an API key, or set the API "
                    "key as the value of the TEXTUAL_API_KEY environment "
                    "variable."
                )
        self.api_key = api_key
        self.client = HttpClient(base_url, self.api_key, verify)
        self.verify = verify

    def get_pipelines(self) -> List[Pipeline]:
        """Get the pipelines for the Tonic Textual instance.

        Returns
        -------
        List[Pipeline]
            A list of pipeline objects, ordered by their creation timestamp.
        Examples
        --------
        >>> latest_pipeline = textual.get_pipelines()[-1]
        """

        with requests.Session() as session:
            response = self.client.http_get("/api/parsejobconfig", session=session)
            pipelines: List[Pipeline] = []
            for x in response:
                pipelines.append(Pipeline(x["name"], x["id"], self.client))
            return pipelines

    def create_s3_pipeline(
        self,
        pipeline_name: str,
        credentials: Optional[PipelineAwsCredential] = None,
        aws_credentials_source: Optional[str] = "user_provided",
        synthesize_files: Optional[bool] = False,
    ) -> S3Pipeline:
        """Create a new pipeline on top of AWS S3

        Parameters
        ----------
        pipeline_name: str
            The name of the pipeline.
        file_source: Optional[str]
            The type of location where the files to process are stored. Possible values are `local`, `aws`, `azure`, and `databricks`. The `local` option allows you to upload files from your local machine.
        credentials: PipelineAwsCredential
            The credentials to use to connect to AWS. Not required when `aws_credentials_source` is `from_environment`.
        synthesize_files: Optional[bool]
            Whether to generate a redacted version of the file in addition to the parsed output.  Default value is `False`.
        aws_credentials_source: Optional[str]
           For an AWS pipeline, how to obtain the AWS credentials.  Options are `user_provided` and `from_environment`.  For `user_provided`, you provide the credentials in the `credentials` parameter.  For `from_environment`, the credentials are read from your Textual instance.

        Returns
        -------
        S3Pipeline
            The newly created pipeline.
        """
        fs = FileSource.aws

        aws_cred_source = AwsCredentialsSource[aws_credentials_source]
        if (
            aws_cred_source == AwsCredentialsSource.user_provided
            and credentials is None
        ):
            raise BadArgumentsException(
                "Must specify AWS credentials when aws_credentials_source = 'user_provided'"
            )

        try:
            object_storage_type = ObjectStorageType.s3
            data = {
                "name": pipeline_name,
                "synthesizeFiles": synthesize_files,
                "fileSource": int(fs.value),
                "objectStorageType": int(object_storage_type.value),
            }

            if credentials is not None:
                data["parseJobExternalCredential"] = {
                    "credential": credentials,
                    "fileSource": int(fs.value),
                }
            if aws_credentials_source is not None and fs == FileSource.aws:
                data["awsCredentialSource"] = aws_cred_source

            p = self.client.http_post("/api/parsejobconfig", data=data)
            return S3Pipeline(p.get("name"), p.get("id"), self.client)
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise PipelineCreateError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def create_azure_pipeline(
        self,
        pipeline_name: str,
        credentials: PipelineAzureCredential,
        synthesize_files: Optional[bool] = False,
    ) -> AzurePipeline:
        """Create a new pipeline on top of Azure blob storage

        Parameters
        ----------
        pipeline_name: str
            The name of the pipeline.
        credentials: PipelineAzureCredential
            The credentials to use to connect to Azure
        synthesize_files: Optional[bool]
            Whether to generate a redacted version of the file in addition to the parsed output.  Default value is `False`.

        Returns
        -------
        AzurePipeline
            The newly created pipeline.
        """
        fs = FileSource.azure

        try:
            object_storage_type = ObjectStorageType.azure
            data = {
                "name": pipeline_name,
                "synthesizeFiles": synthesize_files,
                "fileSource": int(fs.value),
                "objectStorageType": int(object_storage_type.value),
                "parseJobExternalCredential": {
                    "credential": credentials,
                    "fileSource": int(fs.value),
                },
            }
            p = self.client.http_post("/api/parsejobconfig", data=data)
            return AzurePipeline(p.get("name"), p.get("id"), self.client)
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise PipelineCreateError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def create_databricks_pipeline(
        self,
        pipeline_name: str,
        credentials: PipelineDatabricksCredential,
        synthesize_files: Optional[bool] = False,
    ) -> Pipeline:
        """Create a new pipeline on top of Databricks Unity Catalog

        Parameters
        ----------
        pipeline_name: str
            The name of the pipeline.
        credentials: PipelineDatabricksCredential
            The credentials to use to connect to Databricks
        synthesize_files: Optional[bool]
            Whether to generate a redacted version of the file in addition to the parsed output.  Default value is `False`.

        Returns
        -------
        Pipeline
            The newly created pipeline.
        """

        fs = FileSource.databricks

        try:
            object_storage_type = ObjectStorageType.databricks
            data = {
                "name": pipeline_name,
                "synthesizeFiles": synthesize_files,
                "fileSource": int(fs.value),
                "objectStorageType": int(object_storage_type.value),
                "parseJobExternalCredential": {
                    "credential": credentials,
                    "fileSource": int(fs.value),
                },
            }
            p = self.client.http_post("/api/parsejobconfig", data=data)
            return Pipeline(p.get("name"), p.get("id"), self.client)
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise PipelineCreateError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def create_local_pipeline(
        self, pipeline_name: str, synthesize_files: Optional[bool] = False
    ) -> LocalPipeline:
        """Create a new pipeline.

        Parameters
        ----------
        pipeline_name: str
            The name of the pipeline.
        synthesize_files: Optional[bool]
            Whether to generate a redacted version of the file in addition to the parsed output.  Default value is `False`.

        Returns
        -------
        LocalPipeline
            The newly created pipeline.
        """

        try:
            p = self.client.http_post(
                "/api/parsejobconfig/local-files",
                data={"name": pipeline_name, "synthesizeFiles": synthesize_files},
            )
            return LocalPipeline(p.get("name"), p.get("id"), self.client)
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise PipelineCreateError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def create_pipeline(self, pipeline_name: str):
        warn(
            "This method has been deprecated. Please use the new create_s3_pipeline, create_local_pipeline, create_azure_pipeilne, and create_databricks_pipeline specific methods.",
            DeprecationWarning,
            stacklevel=1,
        )

    def delete_pipeline(self, pipeline_id: str):
        """Delete a pipeline.


        Parameters
        ----------
        pipeline_id: str
            The ID of the pipeline.
        """

        try:
            result = self.client.http_delete(f"/api/parsejobconfig/{pipeline_id}")
            return result
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise PipelineDeleteError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def get_pipeline_by_id(self, pipeline_id: str) -> Union[Pipeline, None]:
        """Get the pipeline by ID.

        Parameters
        ----------
        pipeline_id: str
            The ID of the pipeline.

        Returns
        -------
        Union[Pipeline, None]
            The Pipeline object or None if no pipeline is found.
        """

        pipelines = self.get_pipelines()
        found_pipelines = list(filter(lambda x: x.id == pipeline_id, pipelines))
        if len(found_pipelines) == 0:
            return None

        if len(found_pipelines) > 1:
            raise Exception(
                "Found more than 1 pipeline with this ID.  This shouldn't happen."
            )

        return found_pipelines[0]

    def parse_file(
        self, file: io.IOBase, file_name: str, timeout: Optional[int] = None
    ) -> FileParseResult:
        """Parse a given file.  Binary files should be opened with 'rb' option.

        Parameters
        ----------
        file: io.IOBase
            The opened file, available for reading, which will be parsed.
        file_name: str
            The name of the file
        timeout: Optional[int]
            Optional timeout you can set, in seconds, that stops wainting for parsed result after specified time.

        Returns
        -------
        FileParseResult
            The parsed document
        """

        files = {
            "document": (
                None,
                json.dumps({"fileName": file_name, "csvConfig": {}}),
                "application/json",
            ),
            "file": file,
        }

        response = self.client.http_post(
            "/api/parse", files=files, timeout_seconds=timeout
        )
        document = response["document"]
        file_parse_result = response["fileParseResult"]

        return FileParseResult(
            file_parse_result, self.client, False, document=json.loads(document)
        )

    def parse_s3_file(
        self, bucket: str, key: str, timeout: Optional[int] = None
    ) -> FileParseResult:
        """Parse a given file found in S3.  Uses boto3 to fetch files from S3.

        Parameters
        ----------
        bucket: str
            The bucket which contains the file to parse
        key: str
            The key of the file to parse
        timeout: Optional[int]
            Optional timeout you can set, in seconds, that stops wainting for parsed result after specified time.

        Returns
        -------
        FileParseResult
            The parsed document
        """

        import boto3

        s3 = boto3.resource("s3")
        obj = s3.Object(bucket, key)

        file_name = key.split("/")[-1]
        return self.parse_file(obj.get()["Body"].read(), file_name, timeout=timeout)


class TonicTextualParse(TextualParse):
    pass
