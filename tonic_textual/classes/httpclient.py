from typing import Optional
import requests
import os
from urllib3.exceptions import InsecureRequestWarning

from tonic_textual.classes.tonic_exception import (
    ErrorWhenDownloadFile,
    FileNotReadyForDownload,
    LicenseInvalid,
    ParseFileTimeoutException,
    BadRequestDownloadFile,
    TextualServerError,
)

requests.packages.urllib3.disable_warnings(  # type: ignore
    category=InsecureRequestWarning
)


class HttpClient:
    """Client used to handle requests to the Tonic Textual instance.

    Parameters
    ----------
    base_url : str
        URL to the Tonic Textual instance.
    api_key : str
        The API token to use for the requests.
    verify : bool
        Whether to verify SSL certification.
    """

    def __init__(self, base_url: str, api_key: str, verify: bool):
        self.base_url = base_url
        self.headers = {
            "Authorization": api_key,
            "User-Agent": "tonic-textual-python-sdk",
        }
        self.verify = verify

    def http_get_file(
        self,
        url: str,
        session: requests.Session,
        params: dict = {},
        additional_headers={},
    ) -> bytes:
        """Makes a get request to get a file.

        Parameters
        ----------
        url : str
            URL to make the get request. The URL is appended to self.base_url.
        params: dict
            Passed as the params parameter of the requests.get request.

        """
        res = session.get(
            self.base_url + url,
            params=params,
            headers={**self.headers, **additional_headers},
            verify=self.verify,
        )

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 409:
                raise FileNotReadyForDownload("File not yet ready for download")
            if err.response.status_code == 400:
                error_data = err.response.json()
                message_key = "errorMessage"
                if message_key in error_data:
                    raise BadRequestDownloadFile(
                        f"Error Message: {error_data[message_key]}", response=res
                    )
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            raise err

        return res.content

    def http_post_download_file(
        self, url: str, params: dict = {}, data={}, additional_headers={}
    ) -> bytes:
        """Makes a POST request to download a file.

        Parameters
        ----------
        url : str
            URL to make the get request. The URL is appended to self.base_url.
        params: dict
            Passed as the params parameter of the requests.get request.
        data: dict
            Request body.
        additionaHeaders: dict
            Additional HTTP request headers.
        """

        res = requests.post(
            self.base_url + url,
            params=params,
            json=data,
            headers={**self.headers, **additional_headers},
            verify=self.verify,
        )
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 422:
                raise LicenseInvalid(err)
            if err.response.status_code == 409:
                raise FileNotReadyForDownload("File not yet ready for download")
            if err.response.status_code == 500:
                raise ErrorWhenDownloadFile(err)
            else:
                raise err

        return res.content

    def http_get(self, url: str, session: requests.Session, params: dict = {}):
        """Makes a get request.

        Parameters
        ----------
        url : str
            URL to make the get request. The URL is appended to self.base_url.
        params: dict
            Passed as the params parameter of the requests.get request.

        """
        res = session.get(
            self.base_url + url, params=params, headers=self.headers, verify=self.verify
        )

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            raise err

        return res.json()

    def http_post(
        self,
        url,
        params={},
        data={},
        files={},
        additional_headers={},
        timeout_seconds: Optional[int] = None,
    ):
        """Make a post request.

        Parameters
        ----------
        url : str
            URL to make the post request. The URL is appended to self.base_url.
        params: dict
            Passed as the params parameter of the requests.post request.
        data: dict
            Passed as the data parameter of the requests.post request.
        timeout_seconds: Optional[int]
            Timeout in seconds allowed for request
        """

        if (
            timeout_seconds is None
            and os.environ.get("TONIC_TEXTUAL_PARSE_TIMEOUT_IN_SECONDS") is not None
        ):
            try:
                timeout_seconds = int(
                    os.environ.get("TONIC_TEXTUAL_PARSE_TIMEOUT_IN_SECONDS")
                )
            except:  # noqa: E722
                pass

        try:
            res = requests.post(
                self.base_url + url,
                params=params,
                json=data,
                headers={**self.headers, **additional_headers},
                verify=self.verify,
                files=files,
                timeout=timeout_seconds,
            )
        except requests.exceptions.Timeout:
            raise ParseFileTimeoutException()

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 422:
                raise LicenseInvalid(err)
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            else:
                raise err
        if res.content:
            try:
                return res.json()
            except:  # noqa: E722
                return res.text
        else:
            return None

    def http_put(self, url, params={}, data={}, files={}):
        """Makes a put request.

        Parameters
        ----------
        url : str
            URL to make the put request. The URL is appended to self.base_url.
        params: dict
            Passed as the params parameter of the requests.put request.
        data: dict
            Passed as the data parameter of the requests.put request.
        """
        res = requests.put(
            self.base_url + url,
            params=params,
            json=data,
            headers=self.headers,
            verify=self.verify,
        )
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 422:
                raise LicenseInvalid(err)
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            raise err

        return res.json()

    def http_patch(self, url, data={}):
        res = requests.patch(
            self.base_url + url, json=data, headers=self.headers, verify=self.verify
        )

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            raise err

        if res.content:
            return res.json()
        else:
            return None

    def http_delete(self, url, params={}):
        res = requests.delete(
            self.base_url + url, params=params, headers=self.headers, verify=self.verify
        )

        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 500:
                error_data = err.response.json()
                raise TextualServerError(error_data)
            raise err

        if res.content:
            return res.json()
        else:
            return None
