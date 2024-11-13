Redact
=============

The Textual redact functionality allows you to identify entities in files, and then optionally redact/synthesize these entities to create a safe version of your unstructured text.  This functionality works on both raw strings and files, including PDF, DOCX, XLSX, and other formats.

Before you can use these functions, read the :doc:`Getting started <../quickstart/getting_started>` guide and create an API key.

Redacting strings
-----------------

To identify entities in a raw string, call the **redact** function.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TonicTextual("https://textual.tonic.ai")

    raw_redaction = textual.redact("My name is John, and today I am demo-ing Textual, a software product created by Tonic")

The response provides a list of identified entities, with information about each entity.

It also returns a redacted string that replaces the found entities with tokens. You can configure how to handle each type of entities - whether to redact or synthesize them.

To learn more about to redact raw strings, go to :doc:`Redacting text <redacting_text>`.

Redacting files
---------------

Textual can also identify entities within files, including PDF, DOCX, XLSX, CSV, TXT, and various image formats.

Textual can then recreate these files with entities that are redacted or synthesized.

To generated redacted/synthesized files:

.. code-block:: python

   from tonic_textual.redact_api import TextualNer

   redact = TonicTextual("https://textual.tonic.ai")

   with open('<Path to file to redact>', 'rb') as f:
      j = redact.start_file_redaction(f.read(),'<File Name>')

   # Specify generator_config to determine which entities are 'Redacted', 'Synthesis', and 'Off'. 
   # 'Redacted' is the default. To override the default, use the generator_default param.
   new_bytes = redact.download_redacted_file(j)

   with open('<Redacted file name>','wb') as redacted_file:
      redacted_file.write(new_bytes)

To learn more about how to generate redacted and synthesized files, go to :doc:`Redacting files <redacting_files>`.

Working with datasets
---------------------

A dataset is a feature in the Textual UI. It is a collection of files that all share the same redaction/synthesis configuration.

To help automate workflows, you can work with datasets directly from the SDK. To learn more about how you can use the SDK to work with datasets, go to :doc:`Datasets <datasets>`.


.. toctree::
   
   redacting_text
   redacting_files
   datasets
   api
