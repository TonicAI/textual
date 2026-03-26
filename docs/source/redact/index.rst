Synthesize / Redact
====================

The Textual redact functionality allows you to identify entities in text, and then optionally tokenize or synthesize these entities to create a safe version of your unstructured text.

This functionality works on both raw strings and files, including PDF, DOCX, XLSX, and other formats.

Before you can use these functions, read the :doc:`Getting started </index>` guide and create an API key.

When Textual operates on your data:

1. It first identifies sensitive information. Textual can identify 30+ `built-in entity types <https://docs.tonic.ai/textual/entity-types/built-in-entity-types>`_. You can also define your own `custom entity types <https://docs.tonic.ai/textual/entity-types/about-entity-types>`_.

2. Second, it uses information about where entities are located to tokenize or synthesize the data.  

In :doc:`Choosing tokenization or synthesis <./redact_config>` you can learn different ways to configure your output. To fine-tune how synthesized values are generated for specific entity types, see :doc:`Customizing synthesis with generator metadata <./generator_metadata>`.


.. toctree::
   :caption: In this section:

   redact_config
   generator_metadata
   redacting_text
   redacting_json
   redacting_html
   redacting_xml
   redacting_files
   redacting_dataframes
   redacting_large_data
   csv_helper
   api
