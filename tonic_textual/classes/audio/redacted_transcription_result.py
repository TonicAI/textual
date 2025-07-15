from typing import List

from tonic_textual.classes.audio.redact_audio_responses import TranscriptionResult
from tonic_textual.classes.common_api_responses.replacement import Replacement

class RedactedTranscriptionResult(dict):
    """Redaction response object

    Attributes
    ----------
    original_transcript : TranscriptionResult
        The original transcription result
    redacted_text : str
        The redacted and synthesized text of the original transcript. Speaking segments are separated by new lines
    redacted_segments : List[RedactedSegment]
        A list of segments from the original transcript which include the segment text and list of named entities
    usage : int
        The number of words used
    """

    def __init__(
        self,
        original_transcript: TranscriptionResult,
        redacted_text: str,        
        redacted_segments: List[List[Replacement]],
        usage: int,
    ):
        self.original_transcript = original_transcript
        self.redacted_text = redacted_text        
        self.redacted_segments = redacted_segments
        self.usage = usage
        dict.__init__(
            self,
            original_transcript=original_transcript,
            redacted_text=redacted_text,            
            redacted_segments = redacted_segments,
            usage=usage,
        )