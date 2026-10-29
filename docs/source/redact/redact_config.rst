.. _redact-config:

Choosing tokenization or synthesis
====================================

You can configure each Textual built-in and custom entity type. Whether you redact text, json, html, or binary files such as PDF, the configuration is the same. This configuration determines how each entity is handled and ultimately determines the look and feel of your output data.

Available states for entity types
---------------------------------

Each built-in and custom entity type that Textual supports can be set to one of the following states. These states determine what the value looks like in the output.

* Ignored
* Redacted or tokenized
* Synthesized
* Group synthesized

Ignored
^^^^^^^^^^^^
When ignored, an entity is kept as is in the output.

Redaction / Tokenization
^^^^^^^^^^^^^^^^^^^^^^^^^

Tokenized (also referred to as redacted) entities are replaced with *unique* and *reversible* tokens. For example::

    My name is John Smith. -> My name is [NAME_GIVEN_dySb5] [NAME_FAMILY_7w4Db3].

Synthesis
^^^^^^^^^^^^

Synthesized entities are replaced with realistic fake values, For example::

    My name is John Smith. -> My name is Alan Johnson

These fake values are consistent. So in the above example, John changed to Alan and does so in all cases within the document and optionally across documents as well.

To further customize how synthesized values are generated for specific entity types, see :ref:`generator-metadata`.

Group synthesis
^^^^^^^^^^^^^^^^^^

Group synthesized entities are also replaced with realistic values. However, Textual alsoi performs an entity-linking operation.

Configuring handling for entity types
-------------------------------------

To configure how built-in entity types are treated, all SDK functions that operate on data support the ``generator_default`` and ``generator_config`` function parameters.  

``generator_default`` defines the default configuration for all entity types. If not set, the default is ``Redaction``, meaning that entities of all types are redacted or tokenized.

``generator_config`` allows for more fine-grained control. Different entity types can use different options. For example, one common strategy is to set ``generator_default`` to ``Off``. This tells Textual to ignore all entity types. ``generator_config`` is then used to re-enable redaction or synthesis for specific entity types that are relevant to you.

In code, ``generator_default``and ``generator_config`` accept the following possible values, which are case-sensitive.

- ``Off``: Ignores entities
- ``Redaction``: Tokenizes entities
- ``Synthesis``: Standard synthesis with realistic replacement values
- ``GroupingSynthesis``: LLM-based synthesis that maintains contextual relationships between entities

The following example passes a string to the `redact` method. It sets ``generator_default`` to ``Off``, and configures a handful of entity types with ``Synthesis``.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()
    generator_config = {"NAME_GIVEN":"Synthesis", "ORGANIZATION":"Synthesis"}
    raw_synthesis = textual.redact(
        "My name is John, and today I am demoing Textual, a software product created by Tonic", 
        generator_default='Off',
        generator_config=generator_config)
    print(raw_synthesis.describe())

This produces the following output:

.. code-block:: console

    My name is Alfonzo, and today I am demoing Textual, a software product created by New Ignition Worldwide
    {
        "start": 11,
        "end": 15,
        "new_start": 11,
        "new_end": 18,
        "label": "NAME_GIVEN",
        "text": "John",
        "score": 0.9,
        "language": "en",
        "new_text": "Alfonzo"
    }
    {
        "start": 79,
        "end": 84,
        "new_start": 82,
        "new_end": 104,
        "label": "ORGANIZATION",
        "text": "Tonic",
        "score": 0.9,
        "language": "en",
        "new_text": "New Ignition Worldwide"
    }          

Advanced configuration
-----------------------

For built-in entity types, you can use regular expressions to modify the detection. A regular expression can be used to:

* Identify additional values for a given entity type.
* Exclude specified values from a given entity type.

All SDK functions that modify data accept the parameters ``label_allow_lists`` and ``label_block_lists``. These lists are set **for each entity type**.

To start, we'll exclude certain matches from the NAME_FAMILY and ORGANIZATION entity types. Below, we provide a regular expression for NAME_FAMILY. For example, this could prevent 'Wilson' from being tagged as a last name in the below text

.. code-block:: none

    I suffer from Wilson Disease

We'll also exclude from ORGANIZATION any of the exact string matches for Tonic.

.. code-block:: python

    label_block_lists = {
        "NAME_FAMILY": [r'.*\s(Disease|Syndrome|Condition)'],
        "ORGANIZATION": ['tonic','TONIC', 'Tonic']
    }

    ner.redact('<some text here>', label_block_lists = label_block_lists)


Similar to how you use ``label_block_lists`` to exclude text, you can use ``label_allow_lists`` to detect additional values. In the below example, we identify all matches of the below regular expression as HEALTHCARE_ID entity values.

.. code-block:: python

    label_allow_lists = {
        "HEALTHCARE_ID": [r'[a-zA-Z]{2}\-\d{7}']
    }

    ner.redact('<some text here>', label_allow_lists = label_allow_lists)


Custom entity type configuration
--------------------------------

All of the configuration options above also apply to custom entity types.

However, by default, custom entity types are not used unless you explicitly include them in a given request.

Each Python SDK method supports a function parameter called ``custom_entities``. It is a Python list of names of custom entity types to include in the request.

Configuring the labels of a multiclass custom entity type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A multiclass custom entity type is a single model that predicts several labels. A ``generator_config`` key that is the custom entity type name applies to every label that the model predicts.

To configure a single label, use a key of the form ``<CUSTOM_ENTITY>:<LABEL>``. For each detected value, Textual uses the ``<CUSTOM_ENTITY>:<LABEL>`` key if it is present, then the ``<CUSTOM_ENTITY>`` key, and then ``generator_default``.

To list the labels that a multiclass custom entity type's model predicts, use ``get_custom_entity_labels``:

.. code-block:: python

    ner.get_custom_entity_labels("CUSTOM_TREATMENT_DETAILS")
    # ['DOSE', 'MEDICAL_CONDITION', 'MEDICATION']

The list is empty for a model that predicts only the custom entity type itself. It is also empty for a model that was imported before Textual recorded model labels. To list that model's labels, delete the custom entity type and then import it again. Deleting it removes it from every dataset, so you must enable it again on each one.

The following example runs the ``CUSTOM_TREATMENT_DETAILS`` model, but only redacts the values that it labels as ``MEDICAL_CONDITION``:

.. code-block:: python

    ner.redact(
        '<some text here>',
        custom_entities=["CUSTOM_TREATMENT_DETAILS"],
        generator_config={
            "CUSTOM_TREATMENT_DETAILS": "Off",
            "CUSTOM_TREATMENT_DETAILS:MEDICAL_CONDITION": "Redaction",
        },
    )

The custom entity type must still be listed in ``custom_entities``. A ``<CUSTOM_ENTITY>:<LABEL>`` key does not cause the model to run on its own. When you edit a dataset's ``generator_config``, the custom entity type must instead be enabled on the dataset. ``Dataset.edit`` merges ``generator_config`` into the dataset's existing configuration, so to make a label follow the custom entity type's setting again, pass its key in ``removed_generator_config_keys``. A label must start with a letter and contain at most 64 uppercase letters, digits, and underscores.

These keys apply only to ``generator_config``. ``generator_metadata`` is still configured by the custom entity type name.
