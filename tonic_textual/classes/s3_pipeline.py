from typing import List, Optional

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.pipeline import Pipeline


class S3Pipeline(Pipeline):
    """Class to represent and provide access to a Tonic Textual Amazon S3 pipeline.

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

    def set_output_location(self, bucket: str, prefix: Optional[str] = None):
        """Sets the location in Amazon S3 where the pipeline stores processed files.

        Parameters
        ----------
        bucket: str
            The S3 bucket
        prefix: str
            The optional prefix on the bucket
        """

        if bucket.startswith("s3://"):
            bucket = bucket[5:]
        prefix = prefix or ""
        output_location = bucket + "/" + prefix
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"outputPath": output_location}
        )

    def add_prefixes(self, bucket: str, prefixes: List[str]):
        """Adds prefixes to your pipeline. Textual processes all of the files under the prefix that are of supported file types.

        Parameters
        ----------
        bucket: str
            The S3 bucket
        prefix: List[str]
            The list of prefixes to include
        """

        if bucket.startswith("s3://"):
            bucket = bucket[5:]
        path_prefixes = [
            bucket + "/" + prefix
            for prefix in prefixes
            if prefix is not None and len(prefix) > 0
        ]
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"pathPrefixes": path_prefixes}
        )

    def add_files(self, bucket: str, file_paths: List[str]) -> str:
        """Add files to your pipeline

        Parameters
        ----------
        bucket: str
            The S3 bucket
        prefix: List[str]
            The list of files to include
        """

        if bucket.startswith("s3://"):
            bucket = bucket[5:]
        selected_files = [
            bucket + "/" + path
            for path in file_paths
            if path is not None and len(path) > 0
        ]
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"selectedFiles": selected_files}
        )
