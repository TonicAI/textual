Generate redacted audio files
=============================
Textual can also generated a redacted audio file, where PII are replaced with 'beeps'.  This can be accomplished via our :meth:`redact_audio_file<tonic_textual.audio_api.TextualAudio.redact_audio_file>` method.

.. code-block:: python

    from tonic_textual.audio_api import TextualAudio
    from tonic_textual.enums.pii_type import PiiType
    
    textual = TextualAudio()

    # Provide a list of entities to 'beep' out.  If you don't provide a generator_config all entities will be 'beep'-ed out unless generator_default is set to 'Off'
    sensitive_entities=['NAME_GIVEN','NAME_FAMILY']
    gc = {k: 'Off' for k in PiiType if k not in sensitive_entities}
    
    textual.redact_audio('input.mp3','output.mp3', generator_config=gc, generator_default='Off')    


.. rubric:: Additional Remarks

Calling this method requires that pydub be installed in addition to the tonic_textual library.

When using the Textual Cloud (https://textual.tonic.ai) file uploads are limited to 25MB or less.  Supported file types are m4a, mp3, webm, mpga, wav.