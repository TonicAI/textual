import pytest
from tests.utils.resource_utils import get_resource_path

def test_redact_audio_file_does_not_throw(textual_audio):
    path = get_resource_path('banking_customer_support.mp3')
    textual_audio.redact_audio_file(path, 'output.mp3')
