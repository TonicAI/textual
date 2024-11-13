from tonic_textual.classes.enums.file_source import FileSource


class PipelineAzureCredential(dict):
    """Class to represent Azure credentials used to create an Azure pipeline.

    Parameters
    ----------
    account_name: str
        The name of the Azure account from where you plan to access files in Azure Blob Storage.

    account_key: str
        The account key. The key must have access to the Azure Blob Storage containers that you plan to read data from and write data to.
    """

    def __init__(self, account_name: str, account_key: str):
        self.file_source = FileSource.azure

        self.account_name = account_name
        self.account_key = account_key

        dict.__init__(self, accountName=account_name, accountKey=account_key)

    def to_dict(self):
        return {"accountName": self.account_name, "accountKey": self.account_key}
