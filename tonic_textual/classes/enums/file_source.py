from enum import IntEnum


class FileSource(IntEnum):
    local = (0,)
    sharepoint = (1,)
    aws = (2,)
    databricks = (3,)
    sdk = (4,)
    azure = (5,)
