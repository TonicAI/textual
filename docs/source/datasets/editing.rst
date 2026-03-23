Editing a dataset
==================

You can use the SDK to edit a dataset. However, not all dataset properties can be edited from the SDK.

The following snippet renames the dataset and disables modification of entities that are tagged as ORGANIZATION.

.. code-block:: python

    dataset.edit(name='new_dataset_name', generator_config={'ORGANIZATION': 'Off'})