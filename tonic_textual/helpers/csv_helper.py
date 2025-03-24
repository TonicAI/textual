from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from typing import Callable, List
import io
import csv
import uuid

from tonic_textual.helpers.base_helper import BaseHelper

class CsvHelper:
    """A helper class for working with CSV data.  This is useful grouping text across rows to make single API calls which can improve model performance.
    """
    
    def __init__(self):
        self.row_idx_col_name = str(uuid.uuid4())

    def redact_and_reconstruct(self, csv_file: io.BytesIO, has_header: bool, grouping_col: str | None, text_col: str,  redact_func: Callable[[str], RedactionResponse]) -> io.BytesIO:
        """Redacts data in a CSV by joining values from multiple rows into a longer document.  Returns a redacted CSV files, ready to be written to disk.

        Parameters
        ----------
        csv_file: io.Bytes
            The CSV file, passed in as bytes

        has_header: bool
        Whether the first row of the CSV is a header

        grouping_col: str
            The column used for grouping rows. Each group will be converted into a single document. If none provided all rows are grouped together.

        text_col: str
            The column which contains the actual text
        """

        def replace_row_with_redacted_value(row_as_dict: dict, text_col: str, redacted_value: str):
            new_row = row_as_dict.copy()
            new_row[text_col] = redacted_value
            return new_row
        
        def grouping_func(row):            
            return row[grouping_col] if grouping_col is not None else 'constant'
        
        def text_getter_func(row):
            return row[text_col]

        
        response = self.redact(csv_file, has_header, grouping_func, text_getter_func, redact_func)

        #we re-read file, so start at beginning
        csv_file.seek(0)

        reader = csv.reader(csv_file)
        writer_file = io.StringIO()
        writer = csv.writer(writer_file)

        counter = 0
        if has_header:
            header = next(reader)
            writer.writerow(header)
        elif len(response)>0:
            first_row = next(reader)
            header = self.__get_header_when_absent(len(first_row))
            row_as_dict = {h: r for h,r in zip(header,first_row)}
            redacted_row = replace_row_with_redacted_value(row_as_dict, text_col, response[counter].redacted_text)
            writer.writerow([redacted_row[col] for col in header])
            counter = counter + 1

        
        for row in reader:
            row_as_dict = {h: r for h,r in zip(header,row)}
            redacted_row = replace_row_with_redacted_value(row_as_dict, text_col, response[counter].redacted_text)
            writer.writerow([redacted_row[col] for col in header])
            counter = counter + 1

        return writer_file

    def redact(self, csv_file: io.BytesIO, has_header: bool, grouping: Callable[dict, str] | None, text_getter: Callable[[dict], str],  redact_func: Callable[[str], RedactionResponse]) -> List[RedactionResponse]:
        """Redacts data in a CSV by joining values from multiple rows into a longer document.

        Parameters
        ----------
        csv_file: io.Bytes
            The CSV file, passed in as bytes

        has_header: bool
        Whether the first row of the CSV is a header

        grouping: Callable[dict, str] | None
            A function that shows how to group rows.  Each row group will be redacted in a single call. This function takes a row from the CSV and returns a string used to identify the row group.  If none provided all rows are grouped together.

        text_getter: Callable[[dict], str]
            A function to retrieve the relevant text from a given row within a row group.
        """

        if grouping is None:
            # will group all rows together
            def grouping(row):
                return 'constant'

        reader = csv.reader(csv_file)

        row_groups = {}
        row_idx = 0
    
        if has_header:
            header = next(reader)
        else:
            first_row = next(reader)
            self.__group_row(first_row, row_groups, grouping, row_idx)
            row_idx = row_idx + 1
            header = self.__get_header_when_absent(len(first_row))
                
        for row in reader:
            self.__group_row(row, header, row_groups, grouping, row_idx)
            row_idx = row_idx + 1

        response = []
        for group_idx, group in row_groups.items():
            text_list_with_row_idx = [(text_getter(part), part[self.row_idx_col_name]) for part in row_groups[group_idx]]
            text_list = [text_getter(part) for part in row_groups[group_idx]]
            full_text = '\n'.join([text for text in text_list])

            redaction_response = redact_func(full_text)
            starts_and_ends_original = BaseHelper.get_start_and_ends(text_list)      
            
            redacted_lines = BaseHelper.get_redacted_lines(redaction_response, starts_and_ends_original)
            starts_and_ends_redacted = BaseHelper.get_start_and_ends(redacted_lines)
            offset_entities = BaseHelper.offset_entities(redaction_response, starts_and_ends_original, starts_and_ends_redacted)
                            
            for idx, (text, row_idx) in enumerate(text_list_with_row_idx):
                response.append((row_idx, RedactionResponse(text, redacted_lines[idx], -1, offset_entities.get(idx,[]))))
        sorted_response = sorted(response, key=lambda x: x[0])
        return [r for idx,r in sorted_response]

    """Groups rows"""
    def __group_row(self, row: list, header: list, row_groups: dict, grouping_func, row_idx: int):
        if len(row)!=len(header):
            raise Exception('Invalid row. Row must have same number of columns as header.')
        
        row_as_dict = {}
        row_as_dict[self.row_idx_col_name] = row_idx
        for h,r in zip(header, row):
            row_as_dict[h] = r

        group_idx = grouping_func(row_as_dict)
        if group_idx in row_groups:
            row_groups[group_idx].append(row_as_dict)
        else:
            row_groups[group_idx] = []
            row_groups[group_idx].append(row_as_dict)

    def __get_header_when_absent(self, column_count: int) -> List[str]:
        return [str(idx) for idx in range(column_count)]