import json
from typing import Optional, Dict


class Replacement(dict):
    """A span of text that has been detected as a named entity.

    Attributes
    ----------
    start : int
        The start index of the entity in the original text
    end : int
        The end index of the entity in the original text. The end index is exclusive.
    new_start : int
        The start index of the entity in the redacted/synthesized text
    new_end : int
        The end index of the entity in the redacted/synthesized text. The end index is exclusive.
    python_start : Optional[int]
        The start index in Python (if different from start)
    python_end : Optional[int]
        The end index in Python (if different from end)
    label : str
        The label of the entity
    text : str
        The substring of the original text that was detected as an entity
    new_text : Optional[str]
        The new text to replace the original entity
    score : float
        The confidence score of the detection
    language : str
        The language of the entity
    example_redaction : Optional[str]
        An example redaction for the entity
    json_path : Optional[str]
        The JSON path of the entity in the original JSON document. This is only
        present if the input text was a JSON document.
    xml_path : Optional[str]
        The xpath of the entity in the original XML document. This is only present
        if the input text was an XML document.  NOTE: Arrays in xpath are 1-based
    """

    def __init__(
        self,
        start: int,
        end: int,
        new_start: int,
        new_end: int,
        label: str,
        text: str,
        score: float,
        language: str,
        new_text: Optional[str] = None,
        example_redaction: Optional[str] = None,
        json_path: Optional[str] = None,
        xml_path: Optional[str] = None,
    ):
        self.start = start
        self.end = end
        self.new_start = new_start
        self.new_end = new_end
        self.label = label
        self.text = text
        self.new_text = new_text
        self.score = score
        self.language = language
        self.example_redaction = example_redaction
        self.json_path = json_path
        self.xml_path = xml_path

        dict.__init__(
            self,
            start=start,
            end=end,
            new_start=new_start,
            new_end=new_end,
            label=label,
            text=text,
            score=score,
            language=language,
            **({} if new_text is None else {"new_text": new_text}),
            **({} if example_redaction is None else {"example_redaction": example_redaction}),
            **({} if json_path is None else {"json_path": json_path}),
            **({} if xml_path is None else {"xml_path": xml_path}),
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "start": self.start,
            "end": self.end,
            "new_start": self.new_start,
            "new_end": self.new_end,
            "label": self.label,
            "text": self.text,
            "score": self.score,
            "language": self.language,
        }
        if self.new_text is not None:
            out["new_text"] = self.new_text
        if self.example_redaction is not None:
            out["example_redaction"] = self.example_redaction
        if self.json_path is not None:
            out["json_path"] = self.json_path
        if self.xml_path is not None:
            out["xml_path"] = self.xml_path
        return out
