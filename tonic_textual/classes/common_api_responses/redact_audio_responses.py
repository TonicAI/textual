from typing import List

class TranscriptionWord(dict):
    def __init__(
        self,
        start: float,
        end: float,
        word: str
    ):
        self.start = start
        self.end = end
        self.word = word

        dict.__init__(
            self,
            start=start,
            end=end,
            word=word
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

class TranscriptionSegment(dict):
    def __init__(
        self,
        start: float,
        end: float,
        id: int,
        text: str,
        words: List[TranscriptionWord]

    ):
        self.start = start
        self.end = end
        self.id = id
        self.text = text
        self.words = words

        dict.__init__(
            self,
            start=start,
            end=end,
            id=id,
            text=text,
            words=words
        )

    @classmethod
    def from_dict(cls, d):
        words = [TranscriptionWord.from_dict(w) for w in d["words"]]
        return cls(start=d["start"], end=d["end"], id=d["id"], text=d["text"], words=words)


class TranscriptionResult(dict):
    def __init__(
        self,
        text: str,
        segments: TranscriptionSegment,
        language: str = ""
    ):
        self.text = text
        self.segments = segments
        self.language = language

        dict.__init__(
            self,
            text=text,
            segments=segments,
            language=language
        )

    @classmethod
    def from_dict(cls, d):
        segments = [TranscriptionSegment.from_dict(s) for s in d["segments"]]
        return cls(text=d["text"], segments=segments, language=d.get("language", ""))