Generate redacted audio files
=============================
Textual can generate a redacted audio file, where sensitive content is replaced with 'beeps'.

To do this, use the :meth:`redact_audio_file<tonic_textual.audio_api.TextualAudio.redact_audio_file>` method.

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    from tonic_textual.enums.pii_type import PiiType
    
    textual = TextualAudio()

    sensitive_entities=['NAME_GIVEN','NAME_FAMILY']
    gc = {k: 'Redaction' for k in sensitive_entities}
    
    textual.redact_audio('input.mp3','output.mp3', generator_config=gc, generator_default='Off')    


.. rubric:: Additional remarks

Before you call this method, in addition to the ``tonic_textual`` library, you must install pydub.

When you use Textual Cloud (https://textual.tonic.ai), file uploads are limited to 25MB or less.

Textual supports the following audio file types: m4a, mp3, webm, mpga, wav
