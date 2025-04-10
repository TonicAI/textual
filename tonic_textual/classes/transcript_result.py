from typing import List


class TranscriptionWord:
    def __init__(self, start: float, end: float, word: str):
        self.start = start
        self.end = end
        self.text = word
class TranscriptionSegment:
    def __init__(self, start: float, end: float, id: int, text: str, words: List[TranscriptionWord]):
        self.start = start
        self.end = end
        self.id = id
        self.text = text
        self.words = words

class TranscriptionResult:
    def __init__(self, text: str, language: str, segments: List[TranscriptionSegment]):
        self.text = text
        self.language = language
        self.segments = segments