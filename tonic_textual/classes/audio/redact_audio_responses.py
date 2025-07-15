from typing import List

class TranscriptionWord(dict):
    """
    Represents a single word in a transcription, including start and end timestamps.

    Attributes
    ----------
    start : float
        The start time of the word in seconds.
    end : float
        The end time of the word in seconds.
    word : str
        The spoken word.

    """
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
    """
    Represents a segment of the transcription containing text and words with timestamps.

    Attributes
    ----------
    start : float
        The start time of the segment in seconds.
    end : float
        The end time of the segment in seconds.
    id : int
        The segment identifier.
    text : str
        The full text of the segment.
    words : List[TranscriptionWord]
        A list of words included in the segment.

    """
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
    """
    Represents the result of a full transcription, including text, segments, and language.

    Attributes
    ----------
    text : str
        The full transcription text.
    segments : List[TranscriptionSegment]
        The list of transcription segments.
    language : str, optional
        The detected language of the transcription (default is empty string).
    """
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