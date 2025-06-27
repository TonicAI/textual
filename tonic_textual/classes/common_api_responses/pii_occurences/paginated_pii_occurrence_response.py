import json
from typing import Dict, List

from tonic_textual.classes.common_api_responses.pii_occurences.pii_occurrence_response import PiiOccurrenceResponse


class PaginatedPiiOccurrenceResponse(dict):    
    def __init__(
        self,
        offset: int,
        limit: int,
        page_number: int,
        total_pages: int,
        total_records: int,
        has_next_page: bool,
        records: List[PiiOccurrenceResponse]
    ):
        self.offset = offset
        self.limit = limit
        self.page_number = page_number
        self.total_pages = total_pages
        self.total_records = total_records
        self.has_next_page = has_next_page
        self.records = records

        dict.__init__(
            self,
            offset = offset,
            limit = limit,
            page_number = page_number,
            total_pages = total_pages,
            total_records = total_records,
            has_next_page = has_next_page,
            records = records
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "offset": self.offset,
            "limit": self.limit,
            "page_number": self.page_number,
            "total_pages": self.total_pages,
            "total_records": self.total_records,
            "has_next_page": self.has_next_page,
            "records": self.records
        }
        return out