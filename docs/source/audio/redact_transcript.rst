Redacting a transcript
----------------------
Before you can redact a transcript, you must first generate a transcription result. To do this, use the :meth:`get_audio_transcript<tonic_textual.audio_api.TextualAudio.get_audio_transcript>` method. For an example, go to see :doc:`here for an example <generate_transcript>`.

Once you have a transcript, call :meth:`redact_audio_transcript<tonic_textual.audio_api.TextualAudio.redact_audio_transcript>`.

For example:

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    from tonic_textual.enums.pii_type import PiiType
    
    textual = TextualAudio()

    sensitive_entities=['NAME_GIVEN','NAME_FAMILY']
    gc = {k: 'Redaction' for k in sensitive_entities}
    
    transcript = textual.get_audio_transcript('<path to audio file>')

    redacted_transcript = textual.redact_audio_transcript(transcript, generator_config=gc, generator_default='Off').  

The :py:func:`redact_audio_transcript` returns a :class:`redacted_transcript_result<tonic_textual.classes.audio.redacted_transcription_result.RedactedTranscriptionResult>`, which includes:

* The original transcription.
* The redacted or synthesized text of the transcription
* A list of redacted_segments.
* The usage.

.. rubric:: Additional remarks

When you use Textual Cloud (https://textual.tonic.ai), file uploads are limited to 25MB or smaller.

Textual supports the following audio file types: m4a, mp3, webm, mpga, wav

For file types such as m4a, make that sure your build of ffmpeg has the necessary libraries.
