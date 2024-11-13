from typing import Tuple
from enum import Enum

from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult


class FileParseDiffAction(Enum):
    """Enum that stores possible state of a file parse result diff."""
    Added = 1
    """The file was added, so it is new.."""
    Deleted = 2
    """The file was deleted."""
    Modified = 3
    """The file was was modified."""
    NonModified = 4
    """The file was not modified."""


class FileParseResultsDiff(object):
    """Stores file parse result and file parse result action.
    
    Parameters
    ----------
    status : FileParseDiffAction
        The action of the file parse result.

    file : FileParseResult
        The file parse result.
    """
    def __init__(self, status: FileParseDiffAction, file: FileParseResult):
        self.status = status
        self.file = file

    def describe(self) -> str:
        """Returns the status and the file path of the diff as string."""
        return f"{self.status}: {self.file.parsed_file_path}"

    def deconstruct(self) -> Tuple[FileParseDiffAction, FileParseResult]:
        """Returns the status and the file path of the diff."""
        return self.status, self.file
