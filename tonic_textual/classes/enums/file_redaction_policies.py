from enum import Enum


class docx_image_policy(str, Enum):
    redact = 'Redact'
    ignore = 'Ignore'
    remove = 'Remove'


class docx_comment_policy(str, Enum):
    remove = 'Remove'
    ignore = 'Ignore'


class docx_table_policy(str, Enum):
    redact = 'Redact'
    remove = 'Remove'


class pdf_signature_policy(str, Enum):
    redact = 'Redact'
    ignore = 'Ignore'

class pdf_synth_mode_policy(str, Enum):
    V1 = 'V1'
    V2 = 'V2'
