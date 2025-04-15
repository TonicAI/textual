Redact audio files
------------------
Textual supports transcribing audio files and then applying a redaction/synthesis on the transcribed text.  This can be accomplished with our `redact_audio` method:
To redact sensitive information from a text string, pass the string to the `redact` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()

    transcription_redaction = textual.redact_audio("<Path to audio file>")
    print(raw_redaction.describe())

This produces an output identical to our `redact` method.


Additional Remarks
------------------

