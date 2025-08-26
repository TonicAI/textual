from dataclasses import dataclass, field
from typing import List, Optional

from tonic_textual.classes.common_api_responses.replacement import Replacement


@dataclass
class NerEntity:
    start: int
    end: int
    python_start: int
    python_end: int
    label: str
    text: str
    score: float
    language: Optional[str] = None
    example_redaction: Optional[str] = None
    head: Optional[str] = field(default=None, repr=False)
    tail: Optional[str] = field(default=None, repr=False)

def utf16len(c):
    """Returns the length of the single character 'c'
    in UTF-16 code units."""
    return 1 if ord(c) < 65536 else 2

def replacement_to_ner_entity(replacement: Replacement, text: str) -> NerEntity:
    """Convert a Replacement object to a NerEntity object with UTF-16 offsets."""
    # Build UTF-16 offset mapping
    offsets = []
    prev = 0
    for i, c in enumerate(text):
        offset = utf16len(c) - 1
        offsets.append(prev + offset)
        prev = prev + offset
    
    # Calculate C# (UTF-16) indices
    csharp_start = replacement.start + offsets[replacement.start]
    csharp_end = replacement.end + offsets[replacement.end - 1]
    
    return NerEntity(
        start=csharp_start,             # C# UTF-16 index
        end=csharp_end,                 # C# UTF-16 index  
        python_start=replacement.start,  # Python index
        python_end=replacement.end,      # Python index
        label=replacement.label,
        text=replacement.text,
        score=replacement.score,
        language=replacement.language,
        example_redaction=replacement.example_redaction,
        head=None,
        tail=None
    )