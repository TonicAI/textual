Synthesize / Redact
====================

The Textual redact functionality allows you to identify entities in files, and then optionally tokenize or synthesize these entities to create a safe version of your unstructured text. This functionality works on both raw strings and files, including PDF, DOCX, XLSX, and other formats.

Before you can use these functions, read the :doc:`Getting started </index>` guide and create an API key.

Textual operates on your data in a two step process.  First, sensitive information is identified.  Textual supports identification of 30+ built-in entity types which you can read about `here <https://docs.tonic.ai/textual/entity-types/built-in-entity-types>`_.  Textual also supports defining your own `custom entities <https://docs.tonic.ai/textual/entity-types/about-entity-types>`_.  Second, this information of where entities are located is used to then tokenize or synthesize the data.  

In the following section :doc:`Choosing tokenization or synthesis <./redact_config>` you can learn different ways to configure your output.


.. toctree::
   :caption: In this section:
   
   redact_config
   redacting_text
   redacting_json
   redacting_html
   redacting_xml
   redacting_files
   redacting_dataframes
   redacting_large_data
   csv_helper
   api