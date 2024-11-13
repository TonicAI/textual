from typing import Dict, List
from tonic_textual.classes.enums.docx_header_footer_type import DocXHeaderFooterTypeEnum
from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content
from tonic_textual.classes.httpclient import HttpClient


class DocxDocument(BaseDocument):

    def __init__(self, client: HttpClient, json_def):
        super().__init__(client, json_def)
        self.content: Content = Content(client, json_def["content"])
        self.footnotes: List[Content] = [
            Content(client, f) for f in json_def["footNotes"]
        ]
        self.endnotes: List[Content] = [
            Content(client, f) for f in json_def["endNotes"]
        ]
        self.header: Dict[DocXHeaderFooterTypeEnum, Content] = {
            k: Content(client, v) for k, v in json_def["header"].items()
        }
        self.footer: Dict[DocXHeaderFooterTypeEnum, Content] = {
            k: Content(client, v) for k, v in json_def["footer"].items()
        }
