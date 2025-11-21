import json
import uuid
from tonic_textual.classes.parse_api_responses.file_parse_result import FileParseResult
from tonic_textual.classes.enums.file_type import FileTypeEnum
from tonic_textual.parse_api import TonicTextualParse

from tests.utils.resource_utils import get_resource_path


def verify_table_structure(table, expected_structure=None):
    """
    Verify that a table has the expected structure without depending on specific content.

    Args:
        table: The table object to verify
        expected_structure: Optional dictionary with expected metadata like:
            {
                "min_rows": 1,
                "min_cols": 1,
                "header_length": 3,
                "expected_name": "table_name"
            }

    Returns:
        True if verification passes
    """
    # Basic table structure validation
    assert table is not None, "Table should not be None"
    assert hasattr(table, "get_data"), "Table should have get_data method"
    assert hasattr(table, "header"), "Table should have header attribute"
    assert hasattr(table, "table_name"), "Table should have table_name attribute"

    # Table data validation
    data = table.get_data()
    assert isinstance(data, list), "Table data should be a list"
    assert len(data) > 0, "Table data should not be empty"

    # If we have specific expectations, verify them
    if expected_structure:
        if "min_rows" in expected_structure:
            assert len(data) >= expected_structure["min_rows"], (
                f"Table should have at least {expected_structure['min_rows']} rows"
            )

        if "min_cols" in expected_structure:
            assert all(isinstance(row, list) for row in data), (
                "Each row should be a list"
            )
            assert all(len(row) >= expected_structure["min_cols"] for row in data), (
                f"Each row should have at least {expected_structure['min_cols']} columns"
            )

        if "header_length" in expected_structure:
            assert len(table.header) == expected_structure["header_length"], (
                f"Header should have {expected_structure['header_length']} columns"
            )

        if "expected_name" in expected_structure:
            assert table.table_name == expected_structure["expected_name"], (
                f"Table name should be {expected_structure['expected_name']}"
            )

    return True


def verify_markdown_content(markdown_text, min_length=10):
    """
    Verify that markdown content is valid.

    Args:
        markdown_text: The markdown text to verify
        min_length: Minimum expected length

    Returns:
        True if verification passes
    """
    assert markdown_text is not None, "Markdown text should not be None"
    assert isinstance(markdown_text, str), "Markdown text should be a string"
    assert len(markdown_text) >= min_length, (
        f"Markdown text should be at least {min_length} characters long"
    )

    # Check for some basic markdown structure without relying on specific content
    assert markdown_text.strip(), "Markdown text should not be empty"

    return True


def verify_json_content(json_data):
    """
    Verify that JSON content is valid.

    Args:
        json_data: The JSON data to verify

    Returns:
        True if verification passes
    """
    assert json_data is not None, "JSON data should not be None"

    # Check that it's a valid JSON object or array
    try:
        if isinstance(json_data, str):
            parsed = json.loads(json_data)
        else:
            parsed = json_data

        assert isinstance(parsed, (dict, list)), "JSON should be a dictionary or list"
    except json.JSONDecodeError:
        assert False, "JSON data is not valid JSON"

    return True


def verify_tables_by_file_type(file: FileParseResult, expected_counts=None):
    """
    Verify that tables are present as expected for the file type.

    Args:
        file: The FileParseResult object to verify
        expected_counts: Optional dictionary mapping file names to expected table counts

    Returns:
        True if verification passes
    """
    tables = file.get_tables()

    # Default verification based on file type
    if file.file.fileType in (FileTypeEnum.raw, FileTypeEnum.docX):
        assert len(tables) == 0, (
            f"Expected no tables for {file.file.fileName} with type {file.file.fileType}"
        )
        return True

    # If we have specific expectations for this file, verify them
    if expected_counts and file.file.fileName in expected_counts:
        (expected_min, expected_max) = expected_counts[file.file.fileName]

        assert len(tables) >= expected_min, (
            f"Expected minimum of {expected_min} tables for {file.file.fileName}, got {len(tables)}"
        )

        assert len(tables) <= expected_max, (
            f"Expected maximum of {expected_max} tables for {file.file.fileName}, got {len(tables)}"
        )

    # Otherwise, just verify that there's at least one table for known tabular formats
    if file.file.fileType in (FileTypeEnum.csv, FileTypeEnum.xlsx, FileTypeEnum.pdf):
        assert len(tables) > 0, (
            f"Expected at least one table for {file.file.fileName} with type {file.file.fileType}"
        )

    return True


def parse_and_verify_file(
    textual_parse: TonicTextualParse, file_path: str, file_type: str, binary=False
):
    """
    Parse a file and verify the result.

    Args:
        textual_parse: The TonicTextualParse instance to use
        file_path: The path to the file to parse
        file_type: The expected file type
        binary: Whether the file is binary or text

    Returns:
        The parsed file
    """
    # Generate a unique file name
    file_name = f"{uuid.uuid4()}.{file_type}"

    # Read the file
    mode = "rb" if binary else "r"
    with open(get_resource_path(file_path), mode) as f:
        file_bytes = f.read()

    # Parse the file
    parsed_file = textual_parse.parse_file(file_bytes, file_name)

    # Verify the result
    assert parsed_file is not None, f"Parsed file should not be None for {file_path}"

    # Verify markdown content
    markdown = parsed_file.get_markdown()
    verify_markdown_content(markdown)

    # Verify JSON content if available
    if hasattr(parsed_file, "get_json"):
        json_data = parsed_file.get_json()
        verify_json_content(json_data)

    return parsed_file
