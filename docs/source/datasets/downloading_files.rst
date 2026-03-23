Downloading a redacted dataset file
=====================================

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