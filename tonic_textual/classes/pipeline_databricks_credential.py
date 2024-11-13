from tonic_textual.classes.enums.file_source import FileSource


class PipelineDatabricksCredential(dict):
    """Class to represent Databricks credentials used to create a Databricks pipeline.

    Parameters
    ----------
    url: str
        The URL to your Databricks instance.

    access_token: str
        The access token. The token must have access to the Unity Catalog that you plan to read data from and write data to.
    """

    def __init__(self, url: str, access_token: str):
        self.file_source = FileSource.databricks
        self.url = url
        self.access_token = access_token

        dict.__init__(self, url=url, accessToken=access_token)

    def to_dict(self):
        return {"url": self.url, "accessToken": self.access_token}
