📁 Datasets
=========================

A dataset is a collection of files that are all redacted and synthesized in the same way. Datasets are a helpful organization tool to ensure that you can easily track a collections of files and how sensitive data is removed from those files.

Datasets are typically configured from the Textual UI, but for ease of use, the SDK also supports many dataset operations. However, some operations can only be performed from the Textual UI.

Creating a dataset
------------------

To create a dataset:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    
    textual = TonicTextual("https://textual.tonic.ai")
    
    dataset = textual.create_dataset('my_dataset')

Retrieving an existing dataset
------------------------------

To retrieve an existing dataset by the dataset name:

.. code-block:: python

    dataset = textual.get_dataset('my_dataset')


Editing a dataset
-----------------

You can use the SDK to edit a dataset. However, not all properties of the dataset can be edited from the SDK.

The following snippet renames the dataset and disables modification of entities that are tagged as ORGANIZATION.

.. code-block:: python

    dataset.edit(name='new_dataset_name', generator_config={'ORGANIZATION': 'Off'})

Uploading files to a dataset
----------------------------

You can upload files to your dataset from the SDK. Provide the complete path to the file, and the complete name of the file as you want it to appear in Textual.

.. code-block:: python
    
    dataset.add_file('<path to file>','<file name>')

Viewing the list of files in a dataset
--------------------------------------

To get the list of files in a dataset, view the **files** property of the dataset.

To filter dataset files based on their processing status, call:

- **get_failed_files**
- **get_running_files**
- **get_queued_files**
- **get_processed_files**

Downloading a redacted dataset file
-----------------------------------

To download the redacted or synthesized version of the file, get the specific file from the dataset, then call the **download** function.

For example:

.. code-block:: python

    files = dataset.get_processed_files()
    for file in files:
        file_bytes = file.download()
        with open('<file name>', 'wb') as f:
            f.write(file_bytes)

To download a specific file in a dataset that you fetch by name:

.. code-block:: python

    file = txt_file = list(filter(lambda x: x.name=='<file to download>', dataset.files))[0]
    file_bytes = file.download()
    with open('<file name>', 'wb') as f:
        f.write(file_bytes)
