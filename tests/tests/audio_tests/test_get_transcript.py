def test_get_transcription(textual_audio):
    transcript = textual_audio.get_audio_transcript('tests/tests/files/banking_customer_support.mp3')
    assert transcript.language=="english"
    assert len(transcript.segments)>0
    assert len(transcript.text)>100