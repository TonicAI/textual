from typing import Dict, List

from tonic_textual.classes.file_content.content import Content

class Table(dict):
    def __init__(self, data: List[List[Content]], table_name: str, header: List[str]):
        self.table_name = table_name
        self.data = data
        self.header = header
        dict.__init__(
                self,
                table_name = table_name,
                data = data,
                header = header
            )

    def get_data(self) -> List[List[str]]:
        return [[col.text for col in row] for row in self.data]
        
    def to_dict(self) -> Dict:
        return {
            "table_name": self.table_name,
            "data": self.data,
            "header": self.header,
        }