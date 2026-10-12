Files
==================

You can use the SDK to generated redacted and synthesized files. To do this, you can either:

- Redact individual files directly
- Add files to a dataset and then redact them

Before you use the SDK, follow the steps in :doc:`Getting started </index>` to create and set up your API key.

Redact a file
----------------

To redact an individual file:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    #Pass in API Key here, or set TONIC_TEXTUAL_API_KEY in your ENV
    redact = TextualNer()

    with open('<Path to file to redact>', 'rb') as f:
        j = redact.start_file_redaction(f.read(),'<File Name>')

    # Specify generator_config to determine which entity types are 'Redacted', 'Synthesis', and 'Off'. 
    # 'Redacted' is the default. To override the default, use the generator_default param.
    new_bytes = redact.download_redacted_file(j)

    with open('<Redacted file name>','wb') as redacted_file:
        redacted_file.write(new_bytes)

Hard delete a redacted file
---------------------------

Textual keeps the uploaded file and the data that it derives from the file, such as detected entities and OCR results, so that you can download the redacted file again with different settings.

When you no longer need the file, use ``hard_delete_redacted_file`` to permanently delete the uploaded file, its redaction job, and all of the derived data. After you delete the file, you can no longer use the job identifier to download it.

.. code-block:: python

    redact.hard_delete_redacted_file(j)

You can only delete a file after its redaction job finishes. If the file is still being processed, ``hard_delete_redacted_file`` raises ``FileNotReadyForDeletion``.

Configure how to handle specific entity types
----------------------------------------------

By default, in the downloaded file, all of the entities are redacted.

To synthesize values for or ignore specific types of entities in the file, use the ``generator_config`` param.

In this example, we disable the modification of numeric values and synthesize email addresses:

.. code-block:: python

    redact.download_redacted_file(j, generator_config={'NUMERIC_VALUE':'Off','EMAIL_ADDRESS':'Synthesis'})
