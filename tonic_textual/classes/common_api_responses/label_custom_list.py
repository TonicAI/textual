from typing import List, Optional


class LabelCustomList:
    """
    Class to store the custom regex overrides when detecting entities.

    Parameters
    ----------
    regexes : list[str]
        The list of regexes to use when overriding entities.

    """
    def __init__(self, regexes: Optional[List[str]] = None):
        self.regexes = regexes if regexes is not None else []

    def to_dict(self):
        return {
            "regexes": self.regexes
        }