import io
import json
import os
from typing import Optional

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult


class TextualParse:
    """Wrapper class for invoking Tonic Textual API

    Parameters
    ----------
    base_url : Optional[str]
        The URL to your Tonic Textual instance. Do not include trailing backslashes. The default value is https://textual.tonic.ai.
    api_key : Optional[str]
        Optional. Your API token. Instead of providing the API token
        here, we recommended that you set the API key in your environment as the
        value of TEXTUAL_API_KEY.
    verify: bool
        Whether to verify SSL certification verification. By default, this is enabled.
    Examples
    --------
    >>> from tonic_textual.parse_api import TextualParse
    >>> textual = TonicTextualParse("https://textual.tonic.ai")
    """

    def __init__(
        self,
        base_url: str = "https://textual.tonic.ai",
        api_key: Optional[str] = None,
        verify: bool = True,
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

    def parse_file(
        self, file: io.IOBase, file_name: str, timeout: Optional[int] = None
    ) -> FileParseResult:
        """Parse a given file. To open binary files, use the 'rb' option.

        Parameters
        ----------
        file: io.IOBase
            The opened file, available for reading, to parse.
        file_name: str
            The name of the file.
        timeout: Optional[int]
            Optional timeout in seconds. Indicates to stop waiting for the parsed result after the specified time.

        Returns
        -------
        FileParseResult
            The parsed document.
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
            file_parse_result, self.client, document=json.loads(document)
        )

    def parse_s3_file(
        self, bucket: str, key: str, timeout: Optional[int] = None
    ) -> FileParseResult:
        """Parse a given file found in Amazon S3. Uses boto3 to fetch files from Amazon S3.

        Parameters
        ----------
        bucket: str
            The bucket that contains the file to parse.
        key: str
            The key of the file to parse.
        timeout: Optional[int]
            Optional timeout in seconds. Indicates to stop waiting for parsed result after the specified time.

        Returns
        -------
        FileParseResult
            The parsed document.
        """

        import boto3

        s3 = boto3.resource("s3")
        obj = s3.Object(bucket, key)

        file_name = key.split("/")[-1]
        return self.parse_file(obj.get()["Body"].read(), file_name, timeout=timeout)


class TonicTextualParse(TextualParse):
    pass
