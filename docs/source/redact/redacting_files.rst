📄 Files
==================

You can use the SDK to generated redacted and synthesized files. To do this, you can either:

- Redact individual files directly
- Add files to a dataset and then redact them

Before you use the SDK, follow the steps in :doc:`Getting started <../quickstart/getting_started>` to create and set up your API key.

Redacting a file
----------------

To redact an individual file:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    #Pass in API Key here, or set TONIC_TEXTUAL_API_KEY in your ENV
    redact = TonicTextual("https://textual.tonic.ai")

    with open('<Path to file to redact>', 'rb') as f:
        j = redact.start_file_redaction(f.read(),'<File Name>')

    # Specify generator_config to determine which entities are 'Redacted', 'Synthesis', and 'Off'. 
    # 'Redacted' is the default. To override the default, use the generator_default param.
    new_bytes = redact.download_redacted_file(j)

    with open('<Redacted file name>','wb') as redacted_file:
        redacted_file.write(new_bytes)

Configure how to handle specify entity types
--------------------------------------------

By default, the downloaded file redacts all of the entities. To synthesize values for entities and disable specific entities in the file, use the **generator_config** param.

In this example, we disable the modification of numeric values and choose to synthesize email addresses:

.. code-block:: python

    redact.download_redacted_file(j, generator_config={'NUMERIC_VALUE':'Off','EMAIL_ADDRESS':'Synthesis'})
