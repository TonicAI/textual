🧮 Parsing files
=================

When Textual parses files, it convert unstructured files, such as PDF and DOCX, into a more structured JSON form. Textual uses the same JSON schema for all of its supported file types.

To parse a single file, call the **parse_file** function. The function is synchronous. It only returns when the file parsing is complete. For very large files, such as PDFS that are several hundred pages long, this process can take a few minutes.  

To parse a collection of files together, use the Textual dataset functionality. Datasets are best suited for complex tasks that have a large number of files, and where the files are typically housed in stores such as Amazon S3 or Azure Blob Storage. You can manage datasets from the Textual application. Datasets can also track changes to files over time.

To learn more about datasets, go to https://docs.tonic.ai/textual/datasets-create-manage/datasets-flows.

Parsing a local file
---------------------------

To parse a single file from a local file system, start with the following snippet:

.. code-block:: python

    with open('<path to file>','rb') as f:
        byte_data = f.read()
        parsed_doc = textual.parse_file(byte_data, '<file name>')

To read the files, use the 'rb' access mode, which opens the file for read in binary format.

In the **parse_file** command, you can set an optional timeout. The timeout indicates the number of seconds after which to stop waiting for the parsed result.

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

