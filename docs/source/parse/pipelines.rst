👨‍🔧 Pipelines
===============


Textual's pipeline API allows you to extract text and entity metadata from `Textual pipelines <https://docs.tonic.ai/textual/pipelines/pipelines-workflow-for-llm-preparation>`_

Creating a pipeline
--------------------------------
To create a pipeline, use one of the Pipeline create methods

* :meth:`create_local_pipeline<tonic_textual.parse_api.TonicTextualParse.create_local_pipeline>` For uploaded file pipelines
* :meth:`create_s3_pipeline<tonic_textual.parse_api.TonicTextualParse.create_s3_pipeline>` For Amazon S3 pipelines
* :meth:`create_azure_pipeline<tonic_textual.parse_api.TonicTextualParse.create_azure_pipeline>` For Azure pipelines
* :meth:`create_databricks_pipeline<tonic_textual.parse_api.TonicTextualParse.create_databricks_pipeline>` For Databricks pipelines

When you create a pipeline, you provide a name for the pipeline and an optional boolean value to indicate whether to also synthesize the pipeline files. The pipeline creation methods for Amazon S3, Azure, and Databricks also require that you provide credentials.

Creating a local pipeline
--------------------------
To create a local pipeline, you only need to provide a pipeline name.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    pipeline = textual.create_local_pipeline("pipeline name")

Creating and configuring an Amazon S3 pipeline
----------------------------------------------
To create an Amazon S3 pipeline, you must provide some form of AWS credentials to allow Textual to read and write pipeline data to and from Amazon S3.

Use the **aws_credentials_source** parameter to indicate how the credentials are provided. The options are:

* `user_provided`
* `from_environment` - Available for self-hosted instances only.

For `user_provided` credentials, you pass in the IAM credentials when you create the pipeline.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse
    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    creds = PipelineAwsCredential(aws_access_key_id='',aws_region='',aws_secret_access_key='')
    pipeline = textual.create_s3_pipeline('pipeline name', credentials=creds)
    
For `from_environment` credentials, which is only available for self-hosted instances, Textual pulls the AWS credentials directly from the environment where the Textual web server is installed.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse
    from tonic_textual.classes.pipeline_aws_credential import PipelineAwsCredential

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    pipeline = textual.create_s3_pipeline('pipeline name', aws_credentials_source='from_environment')


To configure your pipeline, call any of the following methods:

* :meth:`set_synthesize_files<tonic_textual.classes.pipeline.Pipeline.set_synthesize_files>` - Used to toggle whether to also synthesize files.
* :meth:`set_output_location<tonic_textual.classes.s3_pipeline.S3Pipeline.set_output_location>` - Used to set the location where Textual stores the pipeline output.
* :meth:`add_files<tonic_textual.classes.s3_pipeline.S3Pipeline.add_files>` - Used to add files from an S3 bucket to your pipeline.
* :meth:`add_prefixes<tonic_textual.classes.s3_pipeline.S3Pipeline.add_prefixes>` - Used to add prefixes (folders) to your Amazon S3 pipeline.

Creating and configuring an Azure pipeline
-------------------------------------------
To create an Azure pipeline, pass in the relevant Azure credentials.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse    
    from tonic_textual.classes.pipeline_azure_credential import PipelineAzureCredential

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    
    creds = PipelineAzureCredential(account_name='', account_key='')
    pipeline = textual.create_azure_pipeline('pipeline name', credentials=creds)        

To configure your pipeline, call any of the following methods:

* :meth:`set_synthesize_files<tonic_textual.classes.pipeline.Pipeline.set_synthesize_files>` - Used to toggle whether to also synthesize files.
* :meth:`set_output_location<tonic_textual.classes.azure_pipeline.AzurePipeline.set_output_location>` - Used to setting the location where Textual stores the pipeline output.
* :meth:`add_files<tonic_textual.classes.azure_pipeline.AzurePipeline.add_files>` - Used to add files from Azure to your pipeline.
* :meth:`add_prefixes<tonic_textual.classes.azure_pipeline.AzurePipeline.add_prefixes>` - Used to add prefixes (folders) to your Azure pipeline.

Create a Databricks pipeline
-------------------------------------
To create a Databricks pipeline, pass in the relevant Databricks credentials.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse    
    from tonic_textual.classes.pipeline_databricks_credential import PipelineDatabricksCredential

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    
    creds = PipelineDatabricksCredential(url='', access_token='')
    pipeline = textual.create_databricks_pipeline('pipeline name', credentials=creds)        

Deleting a pipeline
--------------------
To delete a pipeline, use the :meth:`delete_pipeline<tonic_textual.parse_api.TonicTextualParse.delete_pipeline>` method.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    textual.delete_pipeline("<PIPELINE-ID>")    

Getting pipelines
-----------------
The :class:`Pipeline<tonic_textual.classes.pipeline.Pipeline>` class represents a pipeline in Textual.

A pipeline is a collection of jobs that process files and extract text and entities from those files.

To get the list of all of the available pipelines, use the :meth:`get_pipelines<tonic_textual.parse_api.TonicTextualParse.get_pipelines>` method.

.. code-block:: python

    from tonic_textual.parse_api import TextualParse

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    pipelines = textual.get_pipelines()
    latest_pipeline = pipelines[-1]
    print(latest_pipeline.describe())

This produces results similar to the following:

.. code-block:: console

   --------------------------------------------------------
    Name: pipeline demo
    ID: 056e6cc7-0a1d-3ab4-5e61-919fb5475b31
    --------------------------------------------------------

To get a specific pipeline, use the :meth:`get_pipeline_by_id<tonic_textual.parse_api.TonicTextualParse.get_pipeline_by_id>` method.

.. code-block:: python

    pipeline_id = '056e6cc7-0a1d-3ab4-5e61-919fb5475b31'
    textual.get_pipeline_by_id(pipeline_id)


Uploading files
---------------
To upload a file to a pipeline, use the :meth:`upload_file<tonic_textual.classes.pipeline.Pipeline.upload_file>` method.

.. code-block:: python

    pipeline = textual.create_pipeline(pipeline_name)
    with open(file_path, "rb") as file_content:
        file_bytes = file_content.read()
    pipeline.upload_file(file_bytes, file_name)

Enumerating files in a pipeline
-------------------------------
For a pipeline, the :meth:`enumerate_files<tonic_textual.classes.pipeline.Pipeline.enumerate_files>` method returns a :class:`pipeline enumerator<tonic_textual.classes.pipeline_file_enumerator.PipelineFileEnumerator>` of all of the files that the pipeline processed.

By default, this enumerates over the most recent job run of the pipeline. To specify a specific job run, pass the job run identifier as an argument.

.. code-block:: python

    for file in pipeline.enumerate_files():
        print(file.describe())


Enumerating file deltas
-------------------------------
You can determine changes to the files in your pipeline over time.

For example, your pipeline is defined as all of the objects in a given S3 bucket. Over time, the files in the S3 bucket change - files are added and deleted.

Each time you run your pipeline, Textual tracks the delta from the previous run. You can access this delta and determine which files need to be updated, added, or removed.

The following example computes the delta between two successive runs.

.. code-block:: python
    
    runs = pipeline.get_runs()
    delta = runs[1].get_delta(runs[0])
    
    for file in delta:
        status = file.status

        if status=='NotModified':
            continue
        elif status=='Added':
            #handle adding new file content to downstream data store
            pass
        elif status=='Deleted':
            #handle deletion in downstream data store
            pass
