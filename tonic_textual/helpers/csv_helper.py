from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from typing import Callable, List
import io
import csv

from tonic_textual.helpers.base_helper import BaseHelper

class CsvHelper:
    """A helper class for working with CSV data.  This is useful grouping text across rows to make single API calls which can improve model performance.
    """
    
    def __init__(self):
        pass

    def redact(self, csv_file: io.BytesIO, has_header: bool, grouping: Callable[dict, str], ordering: Callable[[dict], [dict]] | None, text_getter: Callable[[dict], str],  redact_func: Callable[[str], RedactionResponse]) -> List[RedactionResponse]:
        """Redacts a conversation.

        Parameters
        ----------
        csv_file: io.Bytes
            The CSV file, passed in as bytes

        has_header: bool
        Whether the first row of the CSV is a header

        grouping: Callable[dict, str]
            A function that shows how to group rows.  Each row group will be redacted in a single call. This function takes a row from the CSV and returns a string used to identify the row group.
            
        ordering: Callable[[dict], list]
            A function which orders the rows in a given group.  If not specified, the original order written to the CSV is preserved

        text_getter: Callable[[dict], str]
            A function to retrieve the relevant text from a given row within a row group.
        """

        reader = csv.reader(csv_file)

        row_groups = {}

        if has_header:
            header = next(reader)
        else:
            first_row = next(reader)
            self.__group_row(first_row, row_groups, grouping_func=grouping)            
            header = [str(idx) for idx in range(len(first_row))]
                
        for row in reader:
            self.__group_row(row, header, row_groups, grouping_func=grouping)

        response = []
        for group_idx, group in row_groups.items():
            ordered_text_parts = ordering(row_groups[group_idx]) if ordering else row_groups[group_idx]
            text_list = [text_getter(part) for part in ordered_text_parts]
            full_text = '\n'.join(text_list)

            redaction_response = redact_func(full_text)
            starts_and_ends_original = BaseHelper.get_start_and_ends(text_list)      
            
            redacted_lines = BaseHelper.get_redacted_lines(redaction_response, starts_and_ends_original)
            starts_and_ends_redacted = BaseHelper.get_start_and_ends(redacted_lines)
            offset_entities = BaseHelper.offset_entities(redaction_response, starts_and_ends_original, starts_and_ends_redacted)
                            
            for idx, text in enumerate(text_list):
                response.append(RedactionResponse(text, redacted_lines[idx], -1, offset_entities.get(idx,[])))
        return response        

    """Groups rows"""
    def __group_row(self, row: list, header: list, row_groups: dict, grouping_func):
        if len(row)!=len(header):
            raise Exception('Invalid row. Row must have same number of columns as header.')
        
        row_as_dict = {}
        for h,r in zip(header, row):
            row_as_dict[h] = r

        group_idx = grouping_func(row_as_dict)
        if group_idx in row_groups:
            row_groups[group_idx].append(row_as_dict)
        else:
            row_groups[group_idx] = []
            row_groups[group_idx].append(row_as_dict)