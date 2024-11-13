import io
import json
from typing import Optional

from requests import RequestException
from tonic_textual.classes.SolarCsvConfig import SolarCsvConfig
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.pipeline import Pipeline
from tonic_textual.classes.tonic_exception import FileUploadError


class LocalPipeline(Pipeline):
    """Class to represent and provide access to a Tonic Textual uploaded local file pipeline.

    Parameters
    ----------
    name: str
        Pipeline name.

    id: str
        Pipeline identifier.

    client: HttpClient
        The HTTP client to use.
    """

    def __init__(self, name: str, id: str, client: HttpClient):
        super().__init__(name, id, client)

    def add_file(
        self,
        file: io.IOBase,
        file_name: str,
        csv_config: Optional[SolarCsvConfig] = None,
    ) -> str:
        """Uploads a file to the pipeline.

        Parameters
        ----------
        file: io.IOBase
            The file to upload.
        file_name: str
            The name of the file.
        csv_config: SolarCsvConfig
            The configuration for the CSV file. This is optional.

        Returns
        -------
        None
            This function does not return any value.
        """
        files = {
            "document": (
                None,
                json.dumps({"fileName": file_name, "csvConfig": csv_config}),
                "application/json",
            ),
            "file": (file_name, file, "application/octet-stream"),
        }

        try:
            return self.client.http_post(
                f"/api/parsejobconfig/{self.id}/local-files/upload", files=files
            )
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise FileUploadError(f"Error {status_code}: {error_message}")
            else:
                raise req_err
