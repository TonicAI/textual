import os
from time import sleep
from typing import List, Optional
from urllib.parse import urlencode
from warnings import warn
import requests

from tonic_textual.classes.subject_collection import SubjectCollection

from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.tonic_exception import (
    SubjectCollectionNameAlreadyExists,
)
from tonic_textual.services.dataset import DatasetService

class TextualSubjects:
    """Wrapper class to invoke the Tonic Textual API

    Parameters
    ----------
    base_url : str
        The URL to your Tonic Textual instance. Do not include trailing backslashes. The default value is https://textual.tonic.ai.
    api_key : str
        Optional. Your API token. Instead of providing the API token
        here, we recommended that you set the API key in your environment as the
        value of TONIC_TEXTUAL_API_KEY.
    verify: bool
        Whether to verify SSL certification. By default, this is enabled.
    Examples
    --------
    >>> from tonic_textual.redact_api import TextualNer
    >>> textual = TextualNer()
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
                    "key as the value of the TONIC_TEXTUAL_API_KEY environment "
                    "variable."
                )

        self.api_key = api_key
        self.client = HttpClient(base_url, self.api_key, verify)
        self.dataset_service = DatasetService(self.client)
        self.verify = verify

    def create_subject_collection(self, collection_name: Optional[str] = None):
        """Creates a subject collection. A collection of 1 or more files for Tonic Textual to scan, group, and synthesize.

        Parameters
        -----
        collection_name : Optional[str] = None
            The name of the collection. Collection names must be unique.  If no name is provided one will be generated randomly


        Returns
        -------
        SubjectCollection
            The newly created collection.


        Raises
        ------

        SubjectCollectionNameAlreadyExists
            Raised if a subject collection with the same name already exists.

        """

        try:
            created = self.client.http_post(
                "/api/dataset", data={"name": collection_name}
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise SubjectCollectionNameAlreadyExists(e)
            raise

        # A subject collection is a regular dataset; subject linking runs on demand via
        # link_subject_collection() rather than a per-dataset toggle.
        return self.get_subject_collection(created["name"])

    def link_subject_collection(
        self,
        collection_name: str,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
        linking_profile: Optional[dict] = None,
    ) -> SubjectCollection:
        """Runs batch subject-linking reconciliation over an entire collection.

        Reconciles every file's detected entities at once into canonical subjects (people,
        organizations, and the identifiers that belong to them) and atomically replaces the
        collection's subject graph. Linking is decoupled from detection, so adding files never
        links on its own — call this after the files finish processing, and again after adding
        more. Re-running is an idempotent full rebuild.

        Parameters
        ----------
        collection_name : str
            The name of the subject collection to link.
        wait : bool
            When True, block until the linking job finishes (or fails / times out) instead of
            returning as soon as it is queued.
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.
        linking_profile : Optional[dict]
            A declarative linking profile describing how subjects are clustered, merged, related,
            and synthesized. When omitted (None), the server uses its built-in default profile.

        Returns
        -------
        SubjectCollection
            The collection that was linked.

        Examples
        --------
        >>> tonic.link_subject_collection("company_emails", wait=True)
        """
        collection = self.get_subject_collection(collection_name)
        collection.link(
            wait=wait,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
            linking_profile=linking_profile,
        )
        return collection

    def delete_subject_collection(self, collection_name: str):
        """Deletes subject collection by name.

        Parameters
        -----
        collection_name : str
            The name of the collection to delete.
        """

        params = {"datasetName": collection_name}
        self.client.http_delete(
            "/api/dataset/delete_dataset_by_name?" + urlencode(params)
        )

    def get_subject_collection(self, collection_name: str) -> SubjectCollection:
        """Gets the subject collection for the specified name.

        Parameters
        ----------
        collection_name : str
            The name of the subject collection.

        Returns
        -------
        SubjectCollection

        Examples
        --------
        >>> collection = tonic.get_subject_collection("company_emails")
        """

        dataset = self.dataset_service.get_dataset(collection_name)
        return SubjectCollection._from_dataset(dataset)

    def get_all_subject_collections(self) -> List[SubjectCollection]:
        """Gets all of the user's subject collections

        Returns
        -------
        List[SubjectCollection]
            The list of all datasets

        Examples
        --------
        >>> collections = tonic.get_all_subject_collections()
        """
        datasets = self.dataset_service.get_all_datasets()

        return [SubjectCollection._from_dataset(dataset) for dataset in datasets]