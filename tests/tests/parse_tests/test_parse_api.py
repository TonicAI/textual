from tests.utils.parse_utils import (
    verify_markdown_content,
    verify_json_content,
    parse_and_verify_file,
)


def test_parse_csv(textual_parse):
    parsed_file = parse_and_verify_file(textual_parse, "simple_file.csv", "csv")
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_raw(textual_parse):
    parsed_file = parse_and_verify_file(textual_parse, "simple_file.txt", "txt")
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_docx(textual_parse):
    parsed_file = parse_and_verify_file(
        textual_parse, "ocean_report.docx", "docx", binary=True
    )
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_xlsx(textual_parse):
    parsed_file = parse_and_verify_file(
        textual_parse,
        "multiple_sheets_multiple_cells_with_inline_strings.xlsx",
        "xlsx",
        binary=True,
    )
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_pdf(textual_parse):
    parsed_file = parse_and_verify_file(
        textual_parse, "Sample Invoice.pdf", "pdf", binary=True
    )
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_img(textual_parse):
    parsed_file = parse_and_verify_file(
        textual_parse, "Coachella.png", "png", binary=True
    )
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_get_json(textual_parse):
    parsed_file = parse_and_verify_file(textual_parse, "simple_file.txt", "txt")
    json_data = parsed_file.get_json()
    verify_json_content(json_data)
