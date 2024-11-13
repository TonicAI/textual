🅰 Text
=========================

Redact raw text
---------------
To redact sensitive information from a text string, pass the string to the `redact` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TonicTextual("https://textual.tonic.ai")

    raw_redaction = textual.redact("My name is John, and today I am demoing Textual, a software product created by Tonic")
    print(raw_redaction.describe())

This produces the following output:

.. code-block:: console

    My name is Alfonzo, and today I am demoing Textual, a software product created by New Ignition Worldwide
    {
        "start": 11,
        "end": 15,
        "new_start": 11,
        "new_end": 29,
        "label": "NAME_GIVEN",
        "text": "John",
        "score": 0.9,
        "language": "en",
        "new_text": "[NAME_GIVEN_dySb5]"
    }
    {
        "start": 79,
        "end": 84,
        "new_start": 93,
        "new_end": 114,
        "label": "ORGANIZATION",
        "text": "Tonic",
        "score": 0.9,
        "language": "en",
        "new_text": "[ORGANIZATION_5Ve7OH]"
    }

Synthesize raw text
-------------------
The following example passes the same string to the `redact` method, but sets some categories to `Synthesis`, which indicates to use realistic replacement values:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")
    generator_config = {"NAME_GIVEN":"Synthesis", "ORGANIZATION":"Synthesis"}
    raw_synthesis = textual.redact(
        "My name is John, and today I am demoing Textual, a software product created by Tonic", 
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

Using LLM synthesis
-------------------
The following example passes the same string to the `llm_synthesis` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")

    raw_synthesis = textual.llm_synthesis("My name is John, and today I am demoing Textual, a software product created by Tonic")
    print(raw_synthesis.describe())

This produces the following output:

.. code-block:: console

    My name is Matthew, and today I am demoing Textual, a software product created by Google.
    {
        "start": 11,
        "end": 15,
        "label": "NAME_GIVEN",
        "text": "John",
        "score": 0.9
    }
    {
        "start": 79,
        "end": 84,
        "label": "ORGANIZATION",
        "text": "Tonic",
        "score": 0.9
    }

Note that LLM Synthesis is non-deterministic — you will likely get different results each time you run.

Redact JSON data
----------------
To redact sensitive information from a JSON string or Python dict, pass the object to the `redact_json` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import json

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")

    d=dict()
    d['person']={'first':'John','last':'OReilly'}
    d['address']={'city': 'Memphis', 'state':'TN', 'street': '847 Rocky Top', 'zip':1234}
    d['description'] = 'John is a man that lives in Memphis.  He is 37 years old and is married to Cynthia'

    json_redaction = textual.redact_json(d, {"LOCATION_ZIP":"Synthesis"})

    print(json.dumps(json.loads(json_redaction.redacted_text), indent=2))

This produces the following output:

.. code-block:: console

    {
    "person": {
        "first": "[NAME_GIVEN_WpFV4]",
        "last": "[NAME_FAMILY_orTxwj3I]"
    },
    "address": {
        "city": "[LOCATION_CITY_UtpIl2tL]",
        "state": "[LOCATION_STATE_n24]",
        "street": "[LOCATION_ADDRESS_KwZ3MdDLSrzNhwB]",
        "zip": 0
    },
    "description": "[NAME_GIVEN_WpFV4] is a man that lives in [LOCATION_CITY_UtpIl2tL].  He is [DATE_TIME_LLr6L3gpNcOcl3] and is married to [NAME_GIVEN_yWfthDa6]"
    }

Redact XML data
----------------
To redact sensitive information from XML, pass the XML document string to the `redact_xml` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import json

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")

    xml_string = '''<?xml version="1.0" encoding="UTF-8"?>
    <!-- This XML document contains sample PII with namespaces and attributes -->
    <PersonInfo xmlns="http://www.example.com/default" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:contact="http://www.example.com/contact">
        <!-- Personal Information with an attribute containing PII -->
        <Name preferred="true" contact:userID="john.doe123">
            <FirstName>John</FirstName>
            <LastName>Doe</LastName>He was born in 1980.</Name>

        <contact:Details>
            <!-- Email stored in an attribute for demonstration -->
            <contact:Email address="john.doe@example.com"/>
            <contact:Phone type="mobile" number="555-6789"/>
        </contact:Details>

        <!-- SSN stored as an attribute -->
        <SSN value="987-65-4321" xsi:nil="false"/>
        <data>his name was John Doe</data>
    </PersonInfo>'''

    xml_redaction = textual.redact_xml(xml_string)

The response includes entity level information, including the XPATH at which the sensitive entity is found. The start and end positions are relative to the beginning of thhe XPATH location where the entity is found.

Redact HTML data
----------------
To redact sensitive information from HTML, pass the HTML document string to the `redact_html` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import json

    textual = TonicTextual("<TONIC-TEXTUAL-URL>")

    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>John Doe</title>
        </head>
        <body>
            <h1>John Doe</h1>
            <p>John Doe is a person who lives in New York City.</p>
            <p>John Doe's phone number is 555-555-5555.</p>
        </body>
    </html>
    """

    xml_redaction = textual.redact_html(html_content)

The response includes entity level information, including the XPATH at which the sensitive entity is found. The start and end positions are relative to the beginning of thhe XPATH location where the entity is found.
