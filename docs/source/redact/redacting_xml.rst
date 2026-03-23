Redact XML data
================
To redact sensitive information from XML, pass the XML document string to the `redact_xml` method.

Like other SDK functions that modify data the `redact_html` allows you to configure how different entity types are treated.  You can learn more about the common parameters:

* generator_default
* generator_config
* label_allow_lists
* label_block_lists

by reading :ref:`redact-config`.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import json

    textual = TextualNer()

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