import uuid

import pytest

from tests.utils.resource_utils import get_resource_path
from tonic_textual.classes.tonic_exception import FileUploadError
from tonic_textual.classes.pipeline import Pipeline


from tests.utils.parse_utils import (
    verify_table_structure,
    verify_tables_by_file_type,
    wait_for_successful_run,
    verify_markdown_content,
    verify_json_content,
    parse_and_verify_file,
)


def test_pipeline_run_all_file_parse_result_functions(
    pipeline_with_files: Pipeline, textual_parse
):
    files = [file for file in pipeline_with_files.enumerate_files()]
    assert len(files) == 5, "Enumerate files did not list all files"
    for file in files:
        md = file.get_markdown(generator_config={"NAME_GIVEN": "Synthesis"})
        verify_markdown_content(md)


def test_tables(pipeline_with_files, textual_parse):
    # Define expected table counts for known files
    expected_counts = {
        "Invoice_1.pdf": 1,
        "utterances_twocol.csv": 1,
        "multiple_sheets_multiple_cells_with_inline_strings.xlsx": 3,
    }

    for file in pipeline_with_files.enumerate_files():
        verify_tables_by_file_type(file, expected_counts)

        # Additional specific structure checks for certain files
        if file.file.fileName == "Invoice_1.pdf":
            table = file.get_tables()[0]
            verify_table_structure(
                table, {"expected_name": "table_0", "header_length": 5}
            )

        if file.file.fileName == "utterances_twocol.csv":
            table = file.get_tables()[0]
            verify_table_structure(
                table, {"expected_name": "csv_table", "header_length": 3}
            )

        if (
            file.file.fileName
            == "multiple_sheets_multiple_cells_with_inline_strings.xlsx"
        ):
            tables = file.get_tables()

            # Check table names and headers without depending on specific content
            sheet_names = [table.table_name for table in tables]
            assert "Sheet1" in sheet_names, "Expected Sheet1 in table names"
            assert "my new sheet" in sheet_names, (
                "Expected 'my new sheet' in table names"
            )
            assert "Sheet3" in sheet_names, "Expected Sheet3 in table names"

            # Verify structure for each sheet
            for table in tables:
                verify_table_structure(table)

                if table.table_name == "Sheet1":
                    assert len(table.header) == 1, (
                        "Sheet1 should have 1 column in header"
                    )
                elif table.table_name == "my new sheet":
                    assert len(table.header) == 1, (
                        "my new sheet should have 1 column in header"
                    )
                elif table.table_name == "Sheet3":
                    assert len(table.header) == 18, (
                        "Sheet3 should have 18 columns in header"
                    )


def test_pipeline_get_runs(pipeline_with_files, textual_parse):
    runs = pipeline_with_files.get_runs()
    assert len(runs) > 0, "Failed to retrieve runs"


def test_upload_file_twice_with_same_name_throws_error(textual_parse):
    pipeline_name = f"test_pipeline_{uuid.uuid4()}"
    pipeline = textual_parse.create_local_pipeline(pipeline_name)

    file_name = f"{uuid.uuid4()}.csv"

    with open(get_resource_path("simple_file.csv"), "r") as f:  # noqa: F821
        file_bytes = f.read()

    try:
        upload_file_response1 = pipeline.add_file(file_bytes, file_name)
        assert upload_file_response1 is None, (
            "Upload failed; successful response should be None without errors."
        )

        with pytest.raises(FileUploadError) as ex:
            pipeline.add_file(file_bytes, file_name)
        expected_error = f"Error 409: File {file_name} already exists in the {pipeline_name} pipeline"
        assert str(ex.value) == expected_error

        # Wait for successful run
        assert wait_for_successful_run(pipeline), "No successful runs found."

        files = pipeline.enumerate_files()
        for file in files:
            content = file.download_results()
            assert content is not None, "Content should not be None."
    finally:
        textual_parse.delete_pipeline(pipeline.id)


def test_parse_csv(textual_parse):
    parsed_file = parse_and_verify_file(textual_parse, "simple_file.csv", "csv")
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_raw(textual_parse):
    parsed_file = parse_and_verify_file(textual_parse, "simple_file.txt", "txt")
    verify_markdown_content(parsed_file.get_markdown())


def test_parse_docx(textual_parse):
    parsed_file = parse_and_verify_file(
        textual_parse, "tonic_msa.docx", "docx", binary=True
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
