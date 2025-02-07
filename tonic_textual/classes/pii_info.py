from typing import Dict, List

from tonic_textual.classes.datasetfile import DatasetFile


class PiiTextExample:
    def __init__(self, data: Dict) -> None:
        self.text: str = data['text']
        self.start_index: int = data['startIndex']
        self.end_index: int = data['endIndex']

    def describe(self) -> Dict:
        return {
            'text': self.text,
            'start_index': self.start_index,
            'end_index': self.end_index
        }


class DatasetFilePiiInfo:
    def __init__(self, data: Dict, name: str) -> None:
        self.name = name
        self.pii_type_counts: Dict[str, int] = data['piiTypeCounts']
        self.pii_text_examples: Dict[str, List[PiiTextExample]] = {
            k: [PiiTextExample(e) for e in v] for k, v in data['piiTextExamples'].items()
        }

    def describe(self) -> Dict:
        return {
            'name': self.name,
            'pii_type_counts': self.pii_type_counts,
            'pii_text_examples': {k: [e.describe() for e in v] for k, v in self.pii_text_examples.items()}
        }


class DatasetPiiInfo:
    def __init__(self, data: Dict, files: List[DatasetFile]) -> None:
        self.file_pii_info: Dict[str, DatasetFilePiiInfo] = {}
        for k, v in data['filePiiInfo'].items():
            file_name = next(file.name for file in files if file.id == k)
            self.file_pii_info[k] = DatasetFilePiiInfo(v, file_name)

    def describe(self) -> Dict:
        return {
            'file_pii_info': {k: v.describe() for k, v in self.file_pii_info.items()}
        }
