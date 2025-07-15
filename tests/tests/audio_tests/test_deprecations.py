import pytest

def test_all_redact_api_audio_functions_warn(textual):
    with pytest.warns(DeprecationWarning):
        textual.redact_audio('')

    with pytest.warns(DeprecationWarning):
        textual.get_audio_transcription('')
    
    with pytest.warns(DeprecationWarning):
        textual.redact_audio_file('','')
