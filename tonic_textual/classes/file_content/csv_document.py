from typing import List
from tonic_textual.classes.file_content.base_document import BaseDocument
from tonic_textual.classes.file_content.content import Content
from tonic_textual.classes.table import Table


class CsvDocument(BaseDocument):

    def __init__(self, client, json_def):
        super().__init__(client, json_def)
        
        table = Table([[Content(client, f) for f in row] for row in json_def["tables"][0]["data"]], json_def["tables"][0]["tableName"], json_def["tables"][0]["header"])
        self.tables: List[Table] = [table]

    def get_cell_content(self, i: int, j: int) -> Content:
        return self.content[i][j]
