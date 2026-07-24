import os
from time import sleep
from typing import List, Optional
from urllib.parse import urlencode
from warnings import warn
import requests

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
