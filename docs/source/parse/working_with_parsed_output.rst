🧞‍♂️ Working with parsed files
================================

After a file is parsed, either directly or as part of a pipeline, you can begin to use the parsed result to build out a data pipeline.

Typically, users build pipelines to feed vector databases for RAG applications, or to prepare datasets to fine-tune or build an LLM.

The parsed result is documented in the Textual documentation in |parsed_structure_external_link|. This topic describes the JSON schema that is used to store the parsed result.

The SDK provides access to the raw JSON in the form of a Python dictionary. It also provides a helper methods and utilities to perform common actions.

Examples of actions that the SDK supports include:

- Get the content of the file in Markdown or plain text
- Redact or synthesize the file content
- Chunk the file. You can redact or synthesize the chunks and also enrich them with additional entity metadata.
- List all of the identified tables and key-value pairs that were found in a document

The below snippet includes most of these supported actions.

.. code-block:: python

    #Content of file, represented in Markdown
    original_markdown = parsed_result.get_markdown()

    #Same Markdown, but specified entities are redacted
    deidentified_markdown = parsed_result.get_markdown(generator_config={'NAME_GIVEN':'Redaction','NAME_FAMILY': 'Redaction','CVV':'Redaction','CREDIT_CARD':'Redaction'})

    #Chunk the file
    parsed_result.get_chunks()

    #Chunk the file, enriched with entity metadata
    parsed_result.get_chunks(metadata_entities=['ORGANIZATION','PRODUCT','LOCATION_CITY'])
    
    #Chunk the file with enrichment, but also redact PII in the chunks
    parsed_result.get_chunks(metadata_entities=['ORGANIZATION','PRODUCT','LOCATION_CITY'], generator_config={'NAME_GIVEN':'Redaction','NAME_FAMILY': 'Redaction'})

    #Get all identified tables found in a PDF
    tables = file.get_tables()

For a list of all of the available operations, go to the :class:`FileParseResult<tonic_textual.classes.parse_api_responses.file_parse_result.FileParseResult>` object documentation.

.. |parsed_structure_external_link| raw:: html

    <a href="https://docs.tonic.ai/textual/pipelines/viewing-pipeline-results/pipeline-json-structure" target="_blank">Parsed JSON structure</a>
