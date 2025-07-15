import re

from tests.utils.resource_utils import get_resource_path

def test_redact_transcript(textual_audio):
    path = get_resource_path('banking_customer_support.mp3')
    transcript = textual_audio.get_audio_transcript(path)
    assert len(transcript.segments)>0, "confirming transcript is likely valid before redacting"

    redacted_transcript = textual_audio.redact_audio_transcript(transcript, generator_default='Off',generator_config={'NAME_GIVEN':'Redaction'})

    assert len(redacted_transcript.redacted_segments)==len(transcript.segments)
    

    NAME_GIVEN_RE = re.compile(r'\[NAME_GIVEN_[^\]]+\]')
    assert bool(NAME_GIVEN_RE.search(redacted_transcript.redacted_text)), "assert we found a redacted first name"