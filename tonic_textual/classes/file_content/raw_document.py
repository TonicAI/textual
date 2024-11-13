from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content
from tonic_textual.classes.httpclient import HttpClient


class RawDocument(BaseDocument):
    def __init__(self, client: HttpClient, json_def):
        super().__init__(client, json_def)
        self.content = Content(client, json_def["content"])
