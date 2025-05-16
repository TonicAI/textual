from typing import Dict, List, Union, Tuple
from tonic_textual.classes.common_api_responses.redact_audio_responses import (
    TranscriptionWord,
    TranscriptionSegment
)
from tonic_textual.classes.common_api_responses.replacement import Replacement
from pydub import AudioSegment
from pydub.generators import Sine
import re

class EnrichedTranscriptionWrod(dict):
    def __init__(
        self,
        start: float,
        end: float,
        word: str,
        char_start: int,
        char_end: int
    ):
        self.start = start
        self.end = end
        self.word = word
        self.char_start = char_start
        self.char_end = char_end

        dict.__init__(
            self,
            start=start,
            end=end,
            word=word,
            char_start=char_start,
            char_end=char_end
        )

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

def add_character_indices_to_words(
    transcript_text: str,
    transcript_words:  List[TranscriptionWord]
) ->  List[EnrichedTranscriptionWrod]:
    """Adds character start/stop indices to transcription word data."""
    enriched_words = []
    offset_index = 0
    for word_obj in transcript_words:
        word = word_obj.word
        for match in re.finditer(re.escape(word), transcript_text[offset_index:]):
            start = match.start() + offset_index
            end = start + len(word)
            enriched_word = EnrichedTranscriptionWrod(
                start=word.start,
                end=word.end,
                word=word.word,
                char_start=start,
                char_end=end
            )
            enriched_words.append(enriched_word)
            offset_index = end
            break     

    return enriched_words

def get_intervals_to_redact(
    transcript_text: str,
    transcript_segments: List[TranscriptionSegment],
    de_identify_results: List[Replacement]
) -> List[Tuple[float, float]]:
    """Converts textual spans to list of timestamp intervals."""
    transcript_words = []
    for segment in transcript_segments:
        transcript_words.extend(segment.words)
    enriched_transcript_words = add_character_indices_to_words(
        transcript_text, transcript_words
    )
    output_intervals = []
    for span in de_identify_results:
        start = span.start
        end = span.end
        intersecting_words: List[TranscriptionWord] = []
        for word_obj in enriched_transcript_words:
            word_start = word_obj.char_start
            word_end = word_obj.char_end
            if start < word_end and word_start < end:
                intersecting_words.append(word_obj)
            if word_start > end: # done
                break
        # unecessary if transcript_words is sorted but cheap
        span_time_start = min([word_obj.start for word_obj in intersecting_words])
        span_time_end = max([word_obj.end for word_obj in intersecting_words])
        output_intervals.append((span_time_start, span_time_end))
    return output_intervals

def redact_audio(
    audio: AudioSegment,
    intervals_to_redact: List[Tuple[float, float]],
    before_eps: float = 250.0,
    after_eps: float = 250.0
) -> AudioSegment:
    for (start, end) in intervals_to_redact:
        # convert seconds to milliseconds
        start_time = (start - before_eps)
        end_time = (end + after_eps)
        segment = audio[start_time:end_time]
        average_volume = segment.dBFS
        beep = Sine(1000).to_audio_segment(
            duration=(end_time - start_time)
        ).apply_gain(average_volume)
        audio = audio[:start_time] + beep + audio[end_time:]
    return audio