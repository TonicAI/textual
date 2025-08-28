from typing import List, Tuple
from tonic_textual.classes.audio.redact_audio_responses import (
    TranscriptionWord,
    TranscriptionSegment
)
from tonic_textual.classes.common_api_responses.replacement import Replacement
from pydub import AudioSegment
from pydub.generators import Sine
import re

class EnrichedTranscriptionWrod(dict):
    """
    A word from a transcription, enriched with character-level indices from the original text.

    Attributes
    ----------
    start : float
        The start time of the word in seconds.
    end : float
        The end time of the word in seconds.
    word : str
        The spoken word.
    char_start : int
        The character start index of the word in the transcript text.
    char_end : int
        The character end index of the word in the transcript text.
    """
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
    """Adds character start and end indices to transcription word data.

    Parameters
    ----------
    transcript_text : str
        The full transcript text.
    transcript_words : List[TranscriptionWord]
        The list of words with timestamp information.

    Returns
    -------
    List[EnrichedTranscriptionWrod]
        The list of words with added character indices for alignment with the original text.
    """
    enriched_words = []
    offset_index = 0
    for word_obj in transcript_words:
        word = word_obj.word
        for match in re.finditer(re.escape(word), transcript_text[offset_index:]):
            start = match.start() + offset_index
            end = start + len(word)
            enriched_word = EnrichedTranscriptionWrod(
                start=word_obj.start,
                end=word_obj.end,
                word=word,
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
    """Converts textual character spans into audio timestamp intervals for redaction.

    Parameters
    ----------
    transcript_text : str
        The full transcript text.
    transcript_segments : List[TranscriptionSegment]
        The list of segments with word-level timing.
    de_identify_results : List[Replacement]
        The list of spans representing sensitive text to redact.

    Returns
    -------
    List[Tuple[float, float]]
        The list of (start, end) timestamp intervals in seconds to redact from the audio.
    """
    transcript_words = []
    for segment in transcript_segments:
        # sometimes the last word of the previous segmant matches the first word of the new segment
        # this causes issues later on if repeats are not removed
        if len(transcript_words) > 0 and len(segment.words) > 0 and segment.words[0] == transcript_words[-1]:
            transcript_words.extend(segment.words[1:])
        else:
            transcript_words.extend(segment.words)
    enriched_transcript_words = add_character_indices_to_words(
        transcript_text, transcript_words
    )
    output_intervals = []
    for span in de_identify_results:
        span_start = span.start
        span_end = span.end
        intersecting_words: List[TranscriptionWord] = []
        for word_obj in enriched_transcript_words:
            word_start = word_obj.char_start
            word_end = word_obj.char_end
            # beep a word if it overlaps with the found span
            # this beeps entire word when span is part of a word
            # overlap can happen in three ways
            # way 1: either word is substring or span or word intersects on the right part of span
            if word_start < span_end and word_start >= span_start:
                intersecting_words.append(word_obj)
            # way 2: either word is substring or span or word intersects on the left part of span
            elif word_end > span_start and word_end <= span_end:
                intersecting_words.append(word_obj)
            # way 3: span is a substring of word
            elif span_start >= word_start and span_end <= word_end:
                intersecting_words.append(word_obj)
            elif word_start > span_end: # done
                break
        # if fail to find intersecting words continue
        if len(intersecting_words) == 0:
            continue
        # unecessary if transcript_words is sorted but cheap
        span_time_start = min([word_obj.start for word_obj in intersecting_words])
        span_time_end = max([word_obj.end for word_obj in intersecting_words])
        output_intervals.append((span_time_start, span_time_end))
    return output_intervals

def redact_audio_segment(
    audio: AudioSegment,
    intervals_to_redact: List[Tuple[float, float]],
    before_eps: float,
    after_eps: float
) -> AudioSegment:
    """Redacts segments of an audio clip by replacing them with a beep sound.

    Parameters
    ----------
    audio : AudioSegment
        The original audio to redact.
    intervals_to_redact : List[Tuple[float, float]]
        The list of intervals in seconds that should be redacted.
    before_eps : float
        The amount of time (in seconds) to include before each redaction interval.
    after_eps : float
        The amount of time (in seconds) to include after each redaction interval.

    Returns
    -------
    AudioSegment
        The redacted audio segment with beeps in place of redacted sections.
    """
    for (start, end) in intervals_to_redact:
        # convert seconds to milliseconds
        start_time = max((start - before_eps), 0)
        end_time = min((end + after_eps), len(audio))
        segment = audio[start_time:end_time]
        average_volume = segment.dBFS
        beep = Sine(1000).to_audio_segment(
            duration=(end_time - start_time)
        ).apply_gain(average_volume)
        audio = audio[:start_time] + beep + audio[end_time:]
    return audio