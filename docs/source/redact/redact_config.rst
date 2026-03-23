Choosing tokenization or synthesis
====================================

Each built-in entity type supported by Textual can be configured.  Whether you are redacting text, json, html, or binary files like PDF the configuration is the same.  This configuration determines how each entity is handled and ultimately determines the look and feel of your output data.

Basic configuration
--------------------

Each built-in and custom entity type supported by Textual can be set to one of four different states.  These states determine what the value looks like in the output.  They are:

Ignored
^^^^^^^^^^^^
When ignored, an entity is left alone in the output

Redaction / Tokenization
^^^^^^^^^^^^^^^^^^^^^^^^^

When tokenized (also referred to as redacted) entities are replaced with *unique* and *reversible* tokens, e.g.::

    My name is John Smith. -> My name is [NAME_GIVEN_dySb5] [NAME_FAMILY_7w4Db3].

Synthesize
^^^^^^^^^^^^

When synthesized, entities are replaced with realistic fake values, e.g.::

    My name is John Smith. -> My name is Alan Johnson

These fake values are consistent. So in the above example, John goes to Alan and will do so in all cases within the document and optionally across documents as well.

Group synthesize
^^^^^^^^^^^^^^^^^^

When group synthesized, entities are also replaced with realistic values however an entity-linking operation is also performed.
   

There are two primary ways to configure how built-in entity types are treated.  All SDK functions that operate on data support the `generator_default` and `generator_config` function parameters.  

`generator_default` defines the default configuration for all entities.  If not set, the default is set to `Redaction` meaning all entity types will be redacted/tokenized.

`generator_config` allows for more fine-grain control.  Different entities can be set to different options.  One common strategy, for example, is to set the `generator_default` to 'Off'.  This will tell Textual to ignore all entity types.  The `generator_config` can then be used to re-enable the specific entity types youc are about.


In code, the `generator_default`and `generator_config` accept the following possible values (case-sensitive).

Textual supports different synthesis options:
- `Off`: Ignores the entity
- `Redaction`: Tokenizes the entity
- `Synthesis`: Standard synthesis with realistic replacement values
- `GroupingSynthesis`: LLM-based synthesis that maintains contextual relationships between entities

The following example passes a string to the `redact` method.  We set the `generator_default` to 'Off' while then specifying a handful of entities as 'Synthesis'.


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

Built-in entity types can be modified via Regex.  Regex can be used to classify more text as a given entity type or less.  All SDK functions that modify data accept the parameters `label_allow_lists` and `label_block_lists`.  These lists are set **per entity**.

Let's start by excluding certain matches from the NAME_FAMILY and ORGANIZATION entity types.  Below, we provide a Regex expression for NAME_FAMILY.  This could, for example, prevent 'Wilson' from being tagged as a last name in the below text

.. code-block:: none

    I suffer from Wilson Disease

We also are excluding from Organization any of the exact string matches for Tonic.

.. code-block:: python

    label_block_lists = {
        "NAME_FAMILY": [r'.*\s(Disease|Syndrome|Condition)'],
        "ORGANIZATION": ['tonic','TONIC', 'Tonic']
    }

    ner.redact('<some text here>', label_block_lists = label_block_lists)


Just like `label_block_lists` can be used to exclude text we can use `label_allow_lists` to bring in additional text.  In the below example, we flag all matches of the below regex to HEALTHCARE_ID.

.. code-block:: python

    label_allow_lists = {
        "HEALTHCARE_ID": [r'[a-zA-Z]{2}\-\d{7}']
    }

    ner.redact('<some text here>', label_allow_lists = label_allow_lists)


Custom entity configuration
----------------------------

All of the configuration options above apply to custom entities as well.  However, by default, custom entities are not used unless explicitly requested in a given request.  Each Python SDK method supports a function parameter called `custom_entities`.  It is a python list of custom entity names to include in the request.
