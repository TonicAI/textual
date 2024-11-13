from typing import Dict


class BaseFile(object):
    def __init__(self, response: Dict):
        self.id = response["id"]
        self.userId = response["userId"]
        self.oid = response["oid"]
        self.fileSizeInKb = response["fileSizeInKb"]
        self.fileName = response["fileName"]
        self.escapeChar = response["escapeChar"]
        self.quoteChar = response["quoteChar"]
        self.hasHeader = response["hasHeader"]
        self.delimiter = response["delimiter"]
        self.nullChar = response["nullChar"]
        self.numRows = response["numRows"]
        self.fileType = response["fileType"]
        self.columnCount = response["columnCount"]
        self.piiTypeCounts = response["piiTypeCounts"]
        self.wordCount = response["wordCount"]
        self.characterCount = response["characterCount"]
        self.redactedWordCount = response["redactedWordCount"]
        self.piiTypes = response["piiTypes"]
        self.piiTypeExamples = response["piiTypeExamples"]
        self.createdDate = response["createdDate"]
        self.lastModifiedDate = response["lastModifiedDate"]
        self.fileHash = response["fileHash"]
        self.fileSource = response["fileSource"]
        self.filePath = response["filePath"]

    def to_dict(self):
        return {
            "textual_id": self.id,
            "userId": self.userId,
            "fileName": self.fileName,
            "fileType": self.fileType,
            "wordCount": self.wordCount,
            "characterCount": self.characterCount,
            "redactedWordCount": self.redactedWordCount,
            "createdDate": self.createdDate,
            "lastModifiedDate": self.lastModifiedDate,
            "fileHash": self.fileHash,
            "fileSource": self.fileSource,
            "filePath": self.filePath,
        }
