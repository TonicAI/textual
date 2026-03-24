Generate transcript
===================
Textual can generate a transcript from an audio file. To do this, use the :meth:`get_audio_transcript<tonic_textual.audio_api.TextualAudio.get_audio_transcript>` method.

To generate a transcript:

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    
    textual = TextualAudio()

    transcription = textual.get_audio_transcript('path_to_file.mp3')

This generates a :class:`transcription_result<tonic_textual.classes.audio.redact_audio_responses.TranscriptionResult>`.

It contains:

* The full text of the transcription.
* The detected language.
* A list of audio segments. Each segment is some portion of the transcription with start and end times in milliseconds.

It looks something like this:

.. literalinclude:: transcription_result.json
  :language: JSON


.. rubric:: Additional remarks

When you use the Textual Cloud (https://textual.tonic.ai), file uploads are limited to 25MB or less.

Textual supports the following file types: m4a, mp3, webm, mpga, wav.

For file types such as m4a, make sure that your build of ffmpeg has the necessary libraries.
