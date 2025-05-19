Redact audio files
------------------
Textual supports transcribing audio files and then applying a redaction/synthesis on the transcribed text.  This can be accomplished with our `redact_audio` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()

    transcription_redaction = textual.redact_audio("<Path to audio file>")
    print(raw_redaction.describe())

This produces an output identical to our `redact` method.

Generate redacted audio
-----------------------
Textual can also generated a redacted audio file, where PII are replaced with 'beeps'.  This can be accomplished via our `redact_audio_file` method:
To generate a redacted audio file

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.enums.pii_type import PiiType
    
    textual = TextualNer()

    # Provide a list of entities to 'beep' out.  If you don't provide a generator_config all entities will be 'beep'-ed out.
    sensitive_entities=['NAME_GIVEN','NAME_FAMILY']
    gc = {k: 'Off' for k in PiiType if k not in sensitive_entities}
    
    textual.redact_audio('input.mp3','output.mp3', generator_config=gc)    

Note that calling this method requires that pydub be installed in addition to the tonic_textual library.

Additional Remarks
------------------
When using the Textual Cloud (https://textual.tonic.ai) file uploads are limited to 25MB or less.  Supported file types are m4a, mp3, webm, mp4, mpga, wav.