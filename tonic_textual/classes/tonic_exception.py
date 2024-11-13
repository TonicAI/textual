from typing import Dict
from requests.exceptions import HTTPError, RequestException


class DatasetNameAlreadyExists(Exception):
    """
    Raised when there is an attempt to create a dataset with a name that already exists.
    """

    def __init__(self, errors):
        # Call the base class constructor with the parameters it needs
        super().__init__(
            "The dataset name already exists. Dataset names must be unique. Choose a "
            "different name."
        )
        self.errors = errors


class DatasetFileMatchesExistingFile(HTTPError):
    """
    Raised when the content in a file to upload matches the content in an existing file
    in the dataset.
    """

    def __init__(self, errors):
        message = (
            "The file content matches content in an existing dataset file. Choose a "
            "different file."
        )

        super().__init__(errors.response.content or message)
        self.errors = errors


class InvalidJsonForRedactionRequest(Exception):
    """
    Raised when the JSON redaction request contains invalid JSON
    """

    def __init__(self, msg):
        super().__init__(msg)


class LicenseInvalid(HTTPError):
    """
    Raised when either your license has expired OR you've exceeded your allowed word
    limit
    """

    def __init__(self, errors):
        super().__init__(
            str(errors.response.content)
            or "Invalid Textual license. Please reach out to textual@tonic.ai."
        )
        self.errors = errors


class FileNotReadyForDownload(Exception):
    """
    Raised when you make a request to download a file that is not yet ready for download
    """

    def __init__(self, msg):
        super().__init__(msg)


class BadArgumentsException(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ErrorWhenDownloadFile(HTTPError):
    """
    Raised when server returns 500 when attempting to download file
    """

    def __init__(self, errors):
        super().__init__(
            "Either error occurred while downloading file or the file redaction job was "
            "cancelled."
        )
        self.errors = errors


class BadRequestDownloadFile(HTTPError):
    """
    Raised when server returns 400 when attempting to download file
    """

    def __init__(self, msg, response=None):
        super().__init__(msg)
        self.response = response


class JobsNotSuccessful(HTTPError):
    """
    Raised when at least one of the jobs in the comparison has not completed successfully
    """

    def __init__(self, errors):
        super().__init__("Both jobs must have completed successfully")
        self.response = errors.response
        self.request = errors.request


class FileUploadError(RequestException):
    """
    Raised when server returns an error when uploading a file
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class DatasetFileNotFound(RequestException):
    """
    Raised when an action is taken on a dataset file that cannot be found in the provided Dataset
    """

    def __init__(self, dataset_name: str, file_id: str):
        message = f"Dataset {dataset_name} does not have a file with id {file_id}"
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class RunPipelineError(RequestException):
    """
    Raised when server returns an error when running pipeline
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class PipelineDeleteError(RequestException):
    """
    Raised when server returns 500 when deleting pipeline
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class PipelineCreateError(RequestException):
    """
    Raised when server returns 500 when creating pipeline
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class DownloadResultFileError(RequestException):
    """
    Raised when server returns 500 when downloading file
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class ParseFileTimeoutException(Exception):
    """
    Raised when parsing an uploaded file takes too long.
    """

    def __init__(self):
        super().__init__(
            "Parsing file took too long.  Either raise the timeout limit by modifying the TONIC_TEXTUAL_PARSE_TIMEOUT_IN_SECONDS or process your file via our pipeline which has no time limits."
        )


class TextualServerError(Exception):
    """
    Raised when the Textual server responds with a 500.
    """

    def __init__(self, error_payload: Dict):
        msg = error_payload["error"]
        super().__init__(msg)
