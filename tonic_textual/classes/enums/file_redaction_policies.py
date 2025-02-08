from enum import Enum

class docx_image_policy(Enum):
    redact = 1
    ignore = 2
    remove = 3

class docx_comment_policy(Enum):
    remove = 1
    ignore = 2

class docx_table_policy(Enum):
    redact = 1
    remove = 2

class pdf_signature_policy(Enum):
    redact = 1
    ignore = 2
