from typing import List


class RecordApiRequestOptions(dict):
    """
    Class to denote whether to record an API request.

    Parameters
    ----------
    record : bool
        Whether to record the request.

    retention_time_in_hours: int
        The number of hours to store the request. The request is then purged automatically.

    tags : List[str]
        A list of tags to assign to the request. Used to help search for the request on the API Explorer page. The default is the empty list [], which corresponds to assigning no tags to the request.
    """
    def __init__(self, record: bool, retention_time_in_hours: int, tags: List[str] = []):
        self.record = record
        self.retention_time_in_hours = retention_time_in_hours
        self.tags = tags

        dict.__init__(
            self,
            record=record,
            retention_time_in_hours=retention_time_in_hours,
            tags = tags
        )

    def to_dict(self):
        return {
            "record": self.record,
            "retention_time_in_hours": self.retention_time_in_hours,
            "tags": self.tags,
        }