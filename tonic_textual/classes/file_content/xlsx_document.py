from typing import Dict, List

from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content
from tonic_textual.classes.httpclient import HttpClient
from tonic_textual.classes.table import Table


class XlsxDocument(BaseDocument):

    def __init__(self, client: HttpClient, json_def):
        super().__init__(client, json_def)
        self.tables: List[Table] = [Table([[Content(client, f) for f in row] for row in table["data"]], table["tableName"], table["header"]) for table in json_def["tables"]]

    def get_cell_content(self, sheet_name: str, i: int, j: int) -> Content:
        return self.content[sheet_name][i][j]
