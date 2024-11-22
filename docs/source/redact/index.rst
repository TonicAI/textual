Redact
=============

The Textual redact functionality allows you to identify entities in files, and then optionally tokenizeor synthesize these entities to create a safe version of your unstructured text. This functionality works on both raw strings and files, including PDF, DOCX, XLSX, and other formats.

Before you can use these functions, read the :doc:`Getting started <../quickstart/getting_started>` guide and create an API key.

Redacting text
-----------------

You can redact text directly in a variety of formats, such as plain text, JSON, XML, and HTML. All redaction requests return a response that includes the original text, redacted text, a list of found entities, and the entity locations. All redact functions also allow you to specify which entities to tokenize and which to synthesize.

The common set of inputs to redact functions are:

* **generator_default**
   The default operation to perform on an entity. The options are 'Redact', 'Synthesis', and 'Off'.
* **generator_config**
   A dictionary where the keys are entity labels and the values are how to redact the entity. The options are 'Redact', 'Synthesis', and 'Off'.
   
   Example: {'NAME_GIVEN': 'Synthesis'}
* **label_allow_lists**
   A dictionary where the keys are entity labels and the values are lists of regular expressions. If a piece of text matches a regular expression, it is flagged as that entity type.
   
   Example: {'HEALTHCARE_ID': [r'[a-zA-zZ]{3}\\d{6,}']
* **label_block_lists**
   A dictionary where the keys are entity labels and the values are lists of regular expressions. If a piece of text matches a regular expression, it is ignored for that entity type.
   
   Example: {'NUMERIC_VALUE': [r'\\d{3}']

The JSON and XML redact functions also have additional inputs, which you can read about in their respective sections.

.. toctree::
   :hidden:
   :maxdepth: 2

   redacting_text

Redacting files
---------------

Textual can also identify entities within files, including PDF, DOCX, XLSX, CSV, TXT, and various image formats.

Textual can then recreate these files with entities that are redacted or synthesized.

To generated redacted and synthesized files:

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

.. toctree::
   :maxdepth: 2
   :hidden:

   redacting_files

Working with datasets
---------------------

A dataset is a feature in the Textual application. It is a collection of files that all share the same redaction and synthesis configuration.

To help automate workflows, you can work with datasets directly from the SDK. To learn more about how to use the SDK to work with datasets, go to :doc:`Datasets <datasets>`.


.. toctree::
   :maxdepth: 2
   :hidden:

   datasets
