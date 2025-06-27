📁 Datasets
=========================

A dataset is a collection of files that are all redacted and synthesized in the same way. Datasets are a helpful organization tool to ensure that you can easily track a collections of files and how sensitive data is removed from those files.

Typically, you configure datasets from the Textual application, but for ease of use, the SDK supports many dataset operations. However, some operations can only be performed from the Textual application.

Creating a dataset
------------------

To create a dataset:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    
    textual = TextualNer()
    
    dataset = textual.create_dataset('my_dataset')

Retrieving an existing dataset
------------------------------

To retrieve an existing dataset by the dataset name:

.. code-block:: python

    dataset = textual.get_dataset('my_dataset')


Editing a dataset
-----------------

You can use the SDK to edit a dataset. However, not all dataset properties can be edited from the SDK.

The following snippet renames the dataset and disables modification of entities that are tagged as ORGANIZATION.

.. code-block:: python

    dataset.edit(name='new_dataset_name', generator_config={'ORGANIZATION': 'Off'})

Uploading files to a dataset
----------------------------

You can upload files to your dataset from the SDK. Provide the complete path to the file, and the complete name of the file as you want it to appear in Textual.

.. code-block:: python
    
    dataset.add_file('<path to file>','<file name>')

Deleting a file from a dataset
------------------------------

To delete a file from the dataset, specify the identifier of the file to delete.

The file identiifer is the value of the **id** property of the dataset file.

.. code-block:: python

    dataset.delete_file('<file identifier>')

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

Viewing the PII information for a dataset
--------------------------------------

You can also retrieve a list of entities found in the files of a dataset.  You can retrieve all entities found or just specific entity types.  The below will retrieve information on ALL entities.

.. code-block:: python

    ds = ner.get_dataset('<dataset name>')

    #retrieve all processed files in the dataset
    files = ds.get_processed_files(refetch=True)    

    for file in files:
        entities = file.get_entities()

It will return a response a dictionary whose key is the type of PII and whose value is a list of found entities.  The returned entity includes the original text value of the entity as well as the few words preceding and following the entity, e.g.

.. literalinclude:: pii_occurence_response.json
  :language: JSON


The call to get_entities() can also take an optional list of entities.  For example, you could pass in a hard coded list as:

.. code-block:: python
    file.get_entities(['NAME_GIVEN','NAME_FAMILY'])

Or do the same using the PiiType enum

.. code-block:: python
    from tonic_textual.enums.pii_type import PiiType
    file.get_entities([PiiType.NAME_GIVEN, PiiType.NAME_FAMILY])

Or you could even just pass in the current set of entities enabled by the dataset configuration, e.g.

.. code-block:: python
    from tonic_textual.enums.pii_state import PiiState

    #Get list of all enabled entities for the dataset
    entities = [k for k in ds.generator_config.keys() if ds.generator_config[k]!=PiiState.Off]
    entities = file.get_entities(entities)
    
    file.get_entities(entities)