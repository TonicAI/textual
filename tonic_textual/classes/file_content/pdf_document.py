from typing import List, Optional
from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content, create_empty_content
from tonic_textual.classes.enums.pdf_content_type import PdfContentTypeEnum
from tonic_textual.classes.enums.pdf_table_cell_type import PdfTableCellTypeEnum
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.table import Table


class PdfPageContent:
    def __init__(self, client: HttpClient, json_def):
        self.type: PdfContentTypeEnum = json_def["type"]
        self.content: Content = Content(client, json_def["content"])


class PdfTableCell:
    def __init__(self, client: HttpClient, json_def):
        self.type: PdfTableCellTypeEnum = json_def["type"]
        self.content: Content = Content(client, json_def["content"])


class PdfTable:
    def __init__(self, client: HttpClient, json_def):
        self.rows: List[List[Optional[PdfTableCell]]] = [
            [PdfTableCell(client, f) if f is not None else None for f in row]
            for row in json_def
        ]


class PdfDocument(BaseDocument):
    def __init__(self, client: HttpClient, json_def):
        super().__init__(client, json_def)
        self.document: Content = Content(client, json_def["content"])
        self.pages: List[List[PdfPageContent]] = [
            [PdfPageContent(client, c) for c in p] for p in json_def["pages"]
        ]

        self.tables: List[Table] = []
        for idx, table in enumerate(json_def["tables"]):
            header = []
            first_row = table[0] if len(table) > 0 else []
            for col in first_row:                
                if col is None or col['type']=="ColumnHeader":
                    header.append(col['content']['text'] if col is not None and col['type']=="ColumnHeader" else "")

            self.tables.append(Table([[Content(client, f["content"] if f is not None else None) for f in row] for row in table], f"table_{idx}", header))
        
        
