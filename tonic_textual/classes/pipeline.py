from typing import List, Optional
from warnings import warn

import requests
import io

from requests import RequestException

from tonic_textual.classes.SolarCsvConfig import SolarCsvConfig
from tonic_textual.classes.file_parse_result_diff_enumerator import (
    FileParseResultsDiffEnumerator,
)
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.pipeline_file_enumerator import PipelineFileEnumerator
from tonic_textual.classes.pipeline_run import PipelineRun
from tonic_textual.classes.tonic_exception import FileUploadError
from abc import ABC


class Pipeline(ABC):
    """Class to represent and provide access to a Tonic Textual pipeline. This class is abstract. Do not instantiate it directly.

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
        self.id = id
        self.name = name
        self.client = client

    def describe(self) -> str:
        """Returns the name and id of the pipeline."""
        description = "--------------------------------------------------------\n"
        description += f"Name: {self.name}\n"
        description += f"ID: {self.id}\n"
        description += "--------------------------------------------------------\n"
        return description

    def get_runs(self) -> List[PipelineRun]:
        """Get the runs for the pipeline.

        Returns
        -------
        List[PipelineRun]
            A list of PipelineRun objects.
        """
        with requests.Session() as session:
            response = self.client.http_get(
                f"/api/parsejob/{self.id}/jobs", session=session
            )
            runs: List[PipelineRun] = []
            for run in response:
                runs.append(
                    PipelineRun(run["id"], run["status"], run["endTime"], self.client)
                )
            return runs

    def run(self) -> str:
        """Run the pipeline.

        Returns
        -------
        str
            The ID of the job.
        """
        try:
            response = self.client.http_post(f"/api/parsejobconfig/{self.id}/start")
            return response
        except RequestException as req_err:
            if hasattr(req_err, "response") and req_err.response is not None:
                status_code = req_err.response.status_code
                error_message = req_err.response.text
                raise FileUploadError(f"Error {status_code}: {error_message}")
            else:
                raise req_err

    def enumerate_files(self, lazy_load_content=True) -> PipelineFileEnumerator:
        """Enumerate the files in the pipeline.

        Parameters
        ----------
        lazy_load_content: bool
            Whether to lazily load the content of the files. Default is True.

        Returns
        -------
        PipelineFileEnumerator
            An enumerator for the files in the pipeline.
        """
        runs = self.get_runs()
        successful_runs = filter(lambda r: r.status == "Completed", runs)
        sorted_finished_runs = sorted(
            successful_runs, key=lambda r: r.end_time, reverse=True
        )

        if len(sorted_finished_runs) == 0:
            return PipelineFileEnumerator(
                "", self.client, lazy_load_content=lazy_load_content
            )

        job_id = sorted_finished_runs[0].id
        return PipelineFileEnumerator(
            job_id, self.client, lazy_load_content=lazy_load_content
        )

    def get_delta(
        self, pipeline_run1: PipelineRun, pipeline_run2: PipelineRun
    ) -> FileParseResultsDiffEnumerator:
        """Enumerates the files in the diff between two pipeline runs.

        Parameters
        ----------
        pipeline_run1: PipelineRun
            The first pipeline run.

        pipeline_run2: PipelineRun
            The second pipeline run.

        Returns
        -------
        FileParseResultsDiffEnumerator
            An enumerator for the files in the diff between the two runs.
        """
        return FileParseResultsDiffEnumerator(
            pipeline_run1.id, pipeline_run2.id, self.client
        )

    def upload_file(
        self,
        file: io.IOBase,
        file_name: str,
        csv_config: Optional[SolarCsvConfig] = None,
    ) -> str:
        warn(
            "This method has been deprecated. Please use the new add_file method",
            DeprecationWarning,
            stacklevel=1,
        )

    def set_synthesize_files(self, synthesize_files: bool):
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"synthesizeFiles": synthesize_files}
        )
