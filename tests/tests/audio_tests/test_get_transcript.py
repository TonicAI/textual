import pytest
from tests.utils.resource_utils import get_resource_path


def test_get_transcription(textual_audio):
    path = get_resource_path("banking_customer_support.mp3")
    transcript = textual_audio.get_audio_transcript(path)
    assert transcript.language == "english" or transcript.language == "en"
    assert len(transcript.segments) > 0
    assert len(transcript.text) > 100
