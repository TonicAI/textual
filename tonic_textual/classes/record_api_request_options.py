from typing import List


class RecordApiRequestOptions(dict):
    """
    Class to denote tags to apply to a recording of an API Request

    Parameters
    ----------
    tags : List[str]
        A list of tags to assign to the request. Used to help search for the request on the Request Auditor page. The default is the empty list [], which corresponds to assigning no tags to the request.
    """

    def __init__(
        self, tags: List[str] = []
    ):
        self.tags = tags

        dict.__init__(
            self,
            tags=tags,
        )

    def to_dict(self):
        return {
            "tags": self.tags,
        }
