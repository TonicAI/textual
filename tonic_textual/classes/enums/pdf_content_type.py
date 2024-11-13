from enum import Enum


class PdfContentTypeEnum(str, Enum):
    page_number = ("PageNumber",)
    page_header = ("PageHeader",)
    page_footer = ("PageFooter",)
    section_heading = ("SectionHeading",)
    pdf_title = ("Title",)
    paragarph = ("Paragraph",)
