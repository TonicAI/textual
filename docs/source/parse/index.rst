Parse
=============

The Textual parse function allows you to convert your unstructured files into a structured JSON payload. You can use the JSON output to build data pipelines to ingest into a vector database, and to build and fine-tune an LLM.

The parse function also uses the Textual NER models to remove sensitive data from your documents and to provide entity enrichment of your data.

To use the Textual SDK to parse files, first read the :doc:`Getting Started <../quickstart/getting_started>` guide and create an API key. Other sections provide details and examples for using specific pieces of the parse functionality.

To learn more about how to use Textual to redact entities within text and files for purposes other than bulding a GenAI system, go to :doc:`Redact <../redact/index>`.

.. toctree:: 
   :caption: In this section:

   parsing_files
   pipelines
   working_with_parsed_output
   api
