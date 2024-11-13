from typing import List
import requests

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult


class PipelineFileEnumerator(object):
    """Enumerates the files in a pipeline.

    Parameters
    ----------
    job_id: str
        The job identifier.

    client: HttpClient
        The HTTP client to use.

    lazy_load_content: bool
        Whether to lazy load the content of the files. Default is True.
    """

    def __init__(self, job_id: str, client: HttpClient, lazy_load_content=True):
        if not isinstance(job_id, str) or job_id == "":
            exception_message = (
                "PipelineFileEnumerator requires a valid job_id.  None or an empty "
                "string was provided."
            )
            raise Exception(exception_message)
        self.job_id = job_id
        self.client = client
        self.lazy_load_content = lazy_load_content

    def __iter__(self):
        self.pagination_token: str = "0"
        self.available_files: List[FileParseResult] = []
        self.idx = 0
        return self

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def next(self) -> FileParseResult:
        if self.idx < len(self.available_files):
            file_to_return = self.available_files[self.idx]
            self.idx = self.idx + 1
            return file_to_return

        if self.pagination_token is None:
            raise StopIteration()

        with requests.Session() as session:
            response = self.client.http_get(
                f"/api/parsejob/{self.job_id}/files?skip={self.pagination_token}",
                session=session,
            )
            self.pagination_token = response["continuationToken"]
            files = response["files"]
            self.available_files = []
            for file in files:
                self.available_files.append(
                    FileParseResult(
                        file, self.client, lazy_load_content=self.lazy_load_content
                    )
                )

        if len(self.available_files) == 0:
            raise StopIteration()

        self.idx = 1
        return self.available_files[0]
