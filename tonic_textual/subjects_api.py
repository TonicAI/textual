import os
from time import sleep
from typing import List, Optional
from urllib.parse import urlencode
from warnings import warn
import requests

from tonic_textual.classes.subject_collection import SubjectCollection
from tonic_textual.classes.subject_graph_collection import SubjectGraph

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

    def create_graph(
        self,
        name: Optional[str] = None,
        synthesize_labels: Optional[List[str]] = None,
        custom_pii_entity_ids: Optional[List[str]] = None,
        label_block_lists: Optional[dict] = None,
    ) -> SubjectGraph:
        """Creates a subject graph — the dataset-free unit of the ``/api/graph`` streaming API.

        Unlike a subject collection (a dataset of uploaded files), a graph holds no files: you
        stream raw text into it with ``SubjectGraph.add_text`` (synchronous, jobless), then
        ``reconcile`` / ``synthesize`` over the whole graph and read each document back with
        ``render_document``.

        Parameters
        ----------
        name : Optional[str] = None
            The name of the graph. Names must be unique. If no name is provided one is generated.
        synthesize_labels : Optional[List[str]] = None
            Built-in PII labels (e.g. ``"NAME_GIVEN"``, ``"EMAIL_ADDRESS"``) to SYNTHESIZE. When this
            or ``custom_pii_entity_ids`` is provided the graph uses an all-or-nothing config: ONLY
            these labels (and the custom entities) are synthesized and every other type is Off
            (detected then passed through unchanged). When both are omitted the graph keeps the broad
            default config.
        custom_pii_entity_ids : Optional[List[str]] = None
            Org-level custom-PII entity ids to detect AND synthesize (e.g. the Slack-mention
            ``username`` entity), so their custom label is detected at ingest and folded into the
            synthesis set.
        label_block_lists : Optional[dict] = None
            Per-label block lists (``{label: LabelCustomList(...).to_dict()}``, same shape the dataset
            PUT used): values of that label that are DETECTED but NOT synthesized (passed through
            unchanged at render). Only honored alongside the all-or-nothing config.

        Returns
        -------
        SubjectGraph
            The newly created graph.

        Raises
        ------
        SubjectCollectionNameAlreadyExists
            Raised if a graph with the same name already exists.

        Examples
        --------
        >>> graph = tonic.create_graph("company_emails")
        """
        body: dict = {"name": name}
        if synthesize_labels is not None:
            body["synthesizeLabels"] = synthesize_labels
        if custom_pii_entity_ids is not None:
            body["customPiiEntityIds"] = custom_pii_entity_ids
        if label_block_lists is not None:
            body["labelBlockLists"] = label_block_lists
        try:
            created = self.client.http_post("/api/graph", data=body)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                raise SubjectCollectionNameAlreadyExists(e)
            raise

        return SubjectGraph(self.client, id=created["id"], name=created.get("name"))

    def get_graph(self, graph_id: str) -> SubjectGraph:
        """Gets an existing subject graph by its id.

        Parameters
        ----------
        graph_id : str
            The id of the graph.

        Returns
        -------
        SubjectGraph

        Examples
        --------
        >>> graph = tonic.get_graph("f3c1...")
        """
        with requests.Session() as session:
            graph = self.client.http_get(f"/api/graph/{graph_id}", session=session)
        return SubjectGraph(self.client, id=graph["id"], name=graph.get("name"))

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

    def synthesize_subject_collection(
        self,
        collection_name: str,
        wait: bool = False,
        timeout_seconds: float = 1800.0,
        poll_interval_seconds: float = 5.0,
    ) -> SubjectCollection:
        """Runs phase 2 of linking — synthesis — over an already-reconciled collection.

        ``link_subject_collection`` only reconciles (groups mentions into subjects without synthetic
        values); this generates the coherent synthetic bundles over that graph, honoring any
        enrichments added in between, and atomically re-persists it. Reuses the profile the reconcile
        ran with. Requires a reconciled graph to exist.

        Parameters
        ----------
        collection_name : str
            The name of the subject collection to synthesize.
        wait : bool
            When True, block until the synthesis job finishes (or fails / times out).
        timeout_seconds : float
            When ``wait`` is True, the maximum time to wait before raising ``TimeoutError``.
        poll_interval_seconds : float
            When ``wait`` is True, how long to sleep between status checks.

        Returns
        -------
        SubjectCollection
            The collection that was synthesized.

        Examples
        --------
        >>> tonic.link_subject_collection("company_emails", wait=True)
        >>> tonic.synthesize_subject_collection("company_emails", wait=True)
        """
        collection = self.get_subject_collection(collection_name)
        collection.synthesize(
            wait=wait,
            timeout_seconds=timeout_seconds,
            poll_interval_seconds=poll_interval_seconds,
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