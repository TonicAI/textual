Generate transcript
===================
Textual can also generated a transcript from an audio file.  This can be accomplished via our :meth:`get_audio_transcript<tonic_textual.audio_api.TextualAudio.get_audio_transcript>` method:
To generate a transcript.

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    
    textual = TextualAudio()

    transcription = textual.get_audio_transcript('path_to_file.mp3')

This will generate a :class:`transcription_result<tonic_textual.classes.audio.redact_audio_responses.TranscriptionResult>`.  It will contain the full text of the transcription, the detected language, and a list of audio segments.  Each segment will be some portion of the transcription with start and end times in milliseconds.

It'll look something like this:

.. literalinclude:: transcription_result.json
  :language: JSON



.. rubric:: Additional Remarks

When using the Textual Cloud (https://textual.tonic.ai) file uploads are limited to 25MB or less.  Supported file types are m4a, mp3, webm, mpga, wav. For file types like m4a you'll need to make sure your build of ffmpeg has the necessary libraries.