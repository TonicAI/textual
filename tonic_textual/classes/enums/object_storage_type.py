from enum import IntEnum


class ObjectStorageType(IntEnum):
    local = (0,)
    s3 = (1,)
    databricks = (2,)
    azure = 5
