Viewing the PII information for a dataset
-----------------------------------------

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

Viewing redaction and synthesis mappings for a dataset
------------------------------------------------------

You can retrieve the original, redacted, synthetic, and final output values for
entities in a dataset after the current generator configuration is applied. The
response is grouped by file.

.. code-block:: python

    ds = ner.get_dataset('<dataset name>')
    mappings = ds.get_entity_mappings()

    for file in mappings.files:
        for entity in file.entities:
            print(file.file_name, entity.text, entity.output_text)