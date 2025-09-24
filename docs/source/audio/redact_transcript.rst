Redacting a transcript
----------------------
To redact a transcript you'll first need to generate a transcription result, which you can do via the :meth:`get_audio_transcript<tonic_textual.audio_api.TextualAudio.get_audio_transcript>` method (see :doc:`here for an example <generate_transcript>`).

Once you have a transcript you can call :meth:`redact_audio_transcript<tonic_textual.audio_api.TextualAudio.redact_audio_transcript>`.  Here is an example:

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    from tonic_textual.enums.pii_type import PiiType
    
    textual = TextualAudio()

    sensitive_entities=['NAME_GIVEN','NAME_FAMILY']
    gc = {k: 'Redaction' for k in sensitive_entities}
    
    transcript = textual.get_audio_transcript('<path to audio file>')

    redacted_transcript = textual.redact_audio_transcript(transcript, generator_config=gc, generator_default='Off').  

The :py:func:`redact_audio_transcript` will return a :class:`redacted_transcript_result<tonic_textual.classes.audio.redacted_transcription_result.RedactedTranscriptionResult>` which will include the original transcription, the redacted/synthesized text of the transcription, a list of redacted_segments, and the usage.

.. rubric:: Additional Remarks

When using the Textual Cloud (https://textual.tonic.ai) file uploads are limited to 25MB or less.  Supported file types are m4a, mp3, webm, mpga, wav. For file types like m4a you'll need to make sure your build of ffmpeg has the necessary libraries.