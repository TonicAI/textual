from typing import List, Optional


class LabelCustomList:
    """
    Class to store the custom regular expression overrides (added or excluded values) to use during entity detection.

    Parameters
    ----------
    regexes : list[str]
        The list of regular expressions to use to override the original entity detection.

    """

    def __init__(self, regexes: Optional[List[str]] = None):
        self.regexes = regexes if regexes is not None else []

    def to_dict(self):
        return {"regexes": self.regexes}
