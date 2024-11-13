import json
from typing import Optional, Dict

class SingleDetectionResult(dict):
    """A span of text that has been detected as a named entity.

    Attributes
    ----------
    start : int
        The start index of the entity in the original text
    end : int
        The end index of the entity in the original text. The end index is exclusive.
    label : str
        The label of the entity
    text : str
        The substring of the original text that was detected as an entity
    score : float
        The confidence score of the detection
    json_path : Optional[str]
        The JSON path of the entity in the original JSON document. This is only
        present if the input text was a JSON document.
    """
    def __init__(
        self,
        start: int,
        end: int,
        label: str,
        text: str,
        score: float,
        json_path: Optional[str] = None,
    ):
        self.start = start
        self.end = end
        self.label = label
        self.text = text
        self.score = score
        self.jsonPath = json_path
        if json_path is None:
            dict.__init__(
                self, start=start, end=end, label=label, text=text, score=score
            )
        else:
            dict.__init__(
                self,
                start=start,
                end=end,
                label=label,
                text=text,
                score=score,
                json_path=json_path,
            )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "start": self.start,
            "end": self.end,
            "label": self.label,
            "text": self.text,
            "score": self.score,
        }
        if self.jsonPath is not None:
            out["jsonPath"] = self.jsonPath
        return out
