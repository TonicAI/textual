from typing import List, Optional

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.pipeline import Pipeline


class AzurePipeline(Pipeline):
    """Class to represent and provide access to a Tonic Textual Azure blob storage pipeline.

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

    def set_output_location(self, container: str, prefix: Optional[str] = None):
        """Sets the location in Azure blob storage where the pipeline stores processed files.

        Parameters
        ----------
        container: str
            The container name.
        prefix: str
            The optional prefix on the container.
        """

        container = self.__prepare_container_name(container)
        prefix = prefix or ""
        output_location = container + "/" + prefix
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"outputPath": output_location}
        )

    def add_prefixes(self, container: str, prefixes: List[str]):
        """Add prefixes to your pipeline. Textual processes all of the files under the prefix that are of supported file types.

        Parameters
        ----------
        container: str
            The container name.
        prefix: List[str]
            The list of prefixes to include.
        """

        container = self.__prepare_container_name(container)
        path_prefixes = [
            container + "/" + prefix
            for prefix in prefixes
            if prefix is not None and len(prefix) > 0
        ]
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"pathPrefixes": path_prefixes}
        )

    def add_files(self, container: str, file_paths: List[str]) -> str:
        """Add files to your pipeline

        Parameters
        ----------
        container: str
            The container name.
        prefix: List[str]
            The list of files to include.
        """

        container = self.__prepare_container_name(container)

        selected_files = [
            container + "/" + path
            for path in file_paths
            if path is not None and len(path) > 0
        ]
        self.client.http_patch(
            f"/api/parsejobconfig/{self.id}", data={"selectedFiles": selected_files}
        )

    def __prepare_container_name(self, container: str) -> str:
        if container.startswith("adfs://"):
            return container[7:]
        elif container.startswith("wasbs://"):
            return container[8:]
        elif container.startswith("azure://"):
            return container[8:]
        else:
            return container
