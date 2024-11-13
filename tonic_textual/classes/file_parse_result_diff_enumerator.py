from typing import List

import requests

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult
from tonic_textual.classes.parse_api_responses.file_parse_results_diff import (
    FileParseResultsDiff,
)
from tonic_textual.classes.tonic_exception import JobsNotSuccessful


class FileParseResultsDiffEnumerator(object):
    """Enumerates the files in a diff between two jobs.

    Parameters
    ----------
    job_id1: str
        The first job identifier.

    job_id2: str
        The second job identifier.

    client: HttpClient
        The HTTP client to use.
    """
    def __init__(self, job_id1: str, job_id2: str, client: HttpClient):
        self.job_id1 = job_id1
        self.job_id2 = job_id2
        self.client = client

    def __iter__(self):
        self.pagination_token: str = "0"
        self.available_files: List[FileParseResultsDiff] = []
        self.idx = 0
        return self

    def __next__(self):
        return self.next()

    def next(self) -> FileParseResultsDiff:
        if self.idx < len(self.available_files):
            file_to_return = self.available_files[self.idx]
            self.idx = self.idx + 1
            return file_to_return

        if self.pagination_token is None:
            raise StopIteration()

        with requests.Session() as session:
            url = "/api/parsejob/"
            url += f"{self.job_id1}/diff/{self.job_id2}?offset={self.pagination_token}"
            try:
                response = self.client.http_get(
                    url,
                    session=session,
                )
            except requests.exceptions.HTTPError as e:
                if "Both jobs must have completed successfully" in e.response.text:
                    raise JobsNotSuccessful(e)
            self.pagination_token = str(response["offset"] + len(response["records"]))
            files = response["records"]
            self.available_files = []
            for file in files:
                file_parse_result = FileParseResult(file["file"], self.client)
                self.available_files.append(
                    FileParseResultsDiff(file["status"], file_parse_result)
                )

        if len(self.available_files) == 0:
            raise StopIteration()

        self.idx = 1
        return self.available_files[0]
