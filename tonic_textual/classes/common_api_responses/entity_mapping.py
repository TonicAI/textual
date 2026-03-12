import json
from typing import Dict, Optional


class EntityMapping(dict):
    """An entity detected in a dataset file and the values it maps to in output."""

    def __init__(
        self,
        label: str,
        text: str,
        redacted_text: Optional[str] = None,
        synthetic_text: Optional[str] = None,
        applied_generator_state: Optional[str] = None,
        output_text: Optional[str] = None,
        row_number: Optional[int] = None,
        column_index: Optional[int] = None,
        score: Optional[float] = None,
    ):
        self.label = label
        self.text = text
        self.redacted_text = redacted_text
        self.synthetic_text = synthetic_text
        self.applied_generator_state = applied_generator_state
        self.output_text = output_text
        self.row_number = row_number
        self.column_index = column_index
        self.score = score

        dict.__init__(
            self,
            label=label,
            text=text,
            **({} if redacted_text is None else {"redacted_text": redacted_text}),
            **({} if synthetic_text is None else {"synthetic_text": synthetic_text}),
            **(
                {}
                if applied_generator_state is None
                else {"applied_generator_state": applied_generator_state}
            ),
            **({} if output_text is None else {"output_text": output_text}),
            **({} if row_number is None else {"row_number": row_number}),
            **({} if column_index is None else {"column_index": column_index}),
            **({} if score is None else {"score": score}),
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "EntityMapping":
        return cls(
            label=data["label"],
            text=data["text"],
            redacted_text=data.get("redactedText"),
            synthetic_text=data.get("syntheticText"),
            applied_generator_state=data.get("appliedGeneratorState"),
            output_text=data.get("outputText"),
            row_number=data.get("rowNumber"),
            column_index=data.get("columnIndex"),
            score=data.get("score"),
        )

    def describe(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_dict(self) -> Dict:
        out = {
            "label": self.label,
            "text": self.text,
        }
        if self.redacted_text is not None:
            out["redacted_text"] = self.redacted_text
        if self.synthetic_text is not None:
            out["synthetic_text"] = self.synthetic_text
        if self.applied_generator_state is not None:
            out["applied_generator_state"] = self.applied_generator_state
        if self.output_text is not None:
            out["output_text"] = self.output_text
        if self.row_number is not None:
            out["row_number"] = self.row_number
        if self.column_index is not None:
            out["column_index"] = self.column_index
        if self.score is not None:
            out["score"] = self.score
        return out
