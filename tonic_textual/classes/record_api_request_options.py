from typing import List, Optional


class RecordApiRequestOptions(dict):
    """
    Class to denote whether/how to record an API request for the Request Auditor.

    Parameters
    ----------
    record : Optional[bool]
        Whether to record the request. When True or None (the default), the request is
        recorded based on the Request Auditor settings defined for your organization. When
        False, the request is never recorded, regardless of the Request Auditor settings.

    tags : List[str]
        A list of tags to assign to the request. Used to help search for the request on the Request Auditor page. The default is the empty list [], which corresponds to assigning no tags to the request.
    """

    def __init__(
        self, record: Optional[bool] = None, tags: List[str] = []
    ):
        self.record = record
        self.tags = tags

        dict.__init__(
            self,
            record=record,
            tags=tags,
        )

    def to_dict(self):
        return {
            "record": self.record,
            "tags": self.tags,
        }
