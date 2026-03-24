Viewing detected entities for a dataset
=======================================

You can retrieve a list of entities that were detected in the dataset files.

Retrieving all entities for a dataset
-------------------------------------

To retrieve the complete list of entities for a dataset:

.. code-block:: python

    ds = ner.get_dataset('<dataset name>')

    #retrieve all processed files in the dataset
    files = ds.get_processed_files(refetch=True)    

    for file in files:
        entities = file.get_entities()

It returns a response in the form of a dictionary where:

* The key is the entity type.
* The value is the list of detected entities of that type.

For each entity, the response includes:

* The original text value of the entity.
* To provide context, a few words that precede and follow the entity.

For example:

.. literalinclude:: pii_occurence_response.json
  :language: JSON

Retrieving specific types of entities for a dataset
---------------------------------------------------

The call to ``get_entities()`` can take an optional list of entity types.

For example, you could pass in a hard-coded list of entity types:

.. code-block:: python
    
    file.get_entities(['NAME_GIVEN','NAME_FAMILY'])

Or you could use the ``PiiType`` enum:

.. code-block:: python

    from tonic_textual.enums.pii_type import PiiType
    file.get_entities([PiiType.NAME_GIVEN, PiiType.NAME_FAMILY])

Retrieving the entities for the enabled entity types for a dataset
------------------------------------------------------------------

To pass in the current set of entities that are enabled by the dataset configuration:

.. code-block:: python

    from tonic_textual.enums.pii_state import PiiState

    #Get list of all enabled entities for the dataset
    entities = [k for k in ds.generator_config.keys() if ds.generator_config[k]!=PiiState.Off]
    entities = file.get_entities(entities)
    
    file.get_entities(entities)

Viewing entity mappings for a dataset
------------------------------------------------------

You can retrieve mappings for each detected entity in a dataset.

.. code-block:: python

    ds = ner.get_dataset('<dataset name>')
    mappings = ds.get_entity_mappings()

    for file in mappings.files:
        for entity in file.entities:
            print(file.file_name, entity.text, entity.output_text)

The response is grouped by file.

Each entity mapping includes:

* The original entity value.
* The redacted version of the entity value.
* The synthesized version of the entity value.
* The final output value based on the current dataset configuration.
