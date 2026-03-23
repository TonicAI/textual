Redact HTML data
=================
To redact sensitive information from HTML, pass the HTML document string to the `redact_html` method.

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