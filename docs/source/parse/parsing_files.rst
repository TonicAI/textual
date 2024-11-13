🧮 Parsing files
=================

When Textual parses files, it convert unstructured files, such as PDF and DOCX, into a more structured JSON form. Textual uses the same JSON schema for all of its supported file types. This SDK also provides utilities that operate on the generated JSON to build data pipelines that you can use to ingest chunks into a vector database or to create data to use to fine-tune and build LLMs.

To parse a single file, call the **parse_file** function. The function is synchronous. It only returns when the file parsing is complete. For very large files, such as PDFS that are several hundred pages long, this process can take a few minutes.  

To parse a collection of files together, use the Textual pipeline functionality. Pipelines are best suited for complex tasks with a large number of files that are typically housed in stores such as Amazon S3 or Azure Blob Storage. You can also manage pipelines from the Textual UI. Pipelines can also track changes to files over time.

To learn more about pipelines, go to the :doc:`getting started guide for pipelines <pipelines>`.

Parsing a local file
---------------------------

To parse a single file from a local file system, start with the following snippet.

.. code-block:: python

    with open('<path to file>','rb') as f:
        byte_data = f.read()
        parsed_doc = textual.parse_file(byte_data, '<file name>')

The files should be read using the 'rb' access mode, which opens the file for read in binary format.

You can optionally set a timeout in the **parse_file** command. The time out indicates the number of seconds after which to stop waiting for the parsed result.

To set a timeout for for all parse requests from the SDK, set the environment variable TONIC_TEXTUAL_PARSE_TIMEOUT_IN_SECONDS.

Parsing a file from Amazon S3
-----------------------------

To parse files from Amazon S3, you pass in a bucket, key pair.

Because this uses the boto3 library to fetch the file from Amazon S3, you must first set up the correct AWS credentials.

.. code-block:: python

    parsed_doc = textual.parse_s3_file('<bucket>','<key>')

Understanding the parsed result
-------------------------------

The parsed result is a :class:`FileParseResult<tonic_textual.classes.parse_api_responses.file_parse_result.FileParseResult>`. It is a wrapper around the JSON that is generated during processing.

To learn more about the structure of the parsed result, go to |parsed_structure_external_link| in the Textual documentation.

.. |parsed_structure_external_link| raw:: html

    <a href="https://docs.tonic.ai/textual/pipelines/viewing-pipeline-results/pipeline-json-structure" target="_blank">Parsed JSON structure</a>
