from typing import List, Optional


class RecordApiRequestOptions(dict):
    """
    Class to denote if an API request should be recorded.

    Parameters
    ----------
    record : bool
        Indicates whether the request should be recorded.

    retention_time_in_hours: int
        The number of hours to store the request.  Afterwards, the request is automatically purged..

    tags : Optional[List[str]]
        An optional list of tags to use for the request.  Makes searching for requests in the UI easier.
    """
    def __init__(self, record: bool, retention_time_in_hours: int, tags: Optional[List[str]] = []):
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