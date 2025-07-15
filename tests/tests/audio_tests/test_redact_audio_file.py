def test_redact_audio_file_does_not_throw(textual_audio):
    textual_audio.redact_audio_file('tests/tests/files/banking_customer_support.mp3', 'output.mp3')
