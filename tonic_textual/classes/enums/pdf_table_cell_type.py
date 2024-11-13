from enum import Enum


class PdfTableCellTypeEnum(str, Enum):
    column_header = ("ColumnHeader",)
    row_header = ("RowHeader",)
    stub_head = ("StubHead",)
    description = ("Description",)
    content = ("Content",)
