Redact text
================
To redact sensitive information from a text string, pass the string to the `redact` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()

    raw_redaction = textual.redact("My name is John, and today I am demoing Textual, a software product created by Tonic")
    print(raw_redaction.describe())

This produces the following output:

.. code-block:: console

    My name is [NAME_GIVEN_HI1h7], and [DATE_TIME_4hKfrH] I am demoing Textual, a software product created by [ORGANIZATION_P5XLAH]
    {
        "start": 11,
        "end": 15,
        "new_start": 11,
        "new_end": 29,
        "label": "NAME_GIVEN",
        "text": "John",
        "score": 0.9,
        "language": "en",
        "new_text": "[NAME_GIVEN_HI1h7]"
    }
    {
        "start": 21,
        "end": 26,
        "new_start": 35,
        "new_end": 53,
        "label": "DATE_TIME",
        "text": "today",
        "score": 0.9,
        "language": "en",
        "new_text": "[DATE_TIME_4hKfrH]"
    }
    {
        "start": 79,
        "end": 84,
        "new_start": 106,
        "new_end": 127,
        "label": "ORGANIZATION",
        "text": "Tonic",
        "score": 0.9,
        "language": "en",
        "new_text": "[ORGANIZATION_P5XLAH]"
    }

You can also record `redact` calls, so that you can view and analyze results in the Textual application. To learn more, read :ref:`record-api-call-section`

Bulk redact raw text
---------------------
In the same way that you use the `redact` method to redact strings, you can use the `redact_bulk` method to redact many strings at the same time.

Each string is redacted individually. Each string is fed into our model independently and cannot affect other strings.

To redact sensitive information from a list of text strings, pass the list to the `redact_bulk` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()

    raw_redaction = textual.redact_bulk(["Tonic was founded in 2018", "John Smith is a person"])
    print(raw_redaction.describe())

This produces the following output:

.. code-block:: console

    [ORGANIZATION_5Ve7OH] was founded in [DATE_TIME_DnuC1]
    {
        "start": 0,
        "end": 5,
        "new_start": 0,
        "new_end": 21,
        "label": "ORGANIZATION",
        "text": "Tonic",
        "score": 0.9,
        "language": "en",
        "new_text": "[ORGANIZATION_5Ve7OH]"
    }
    {
        "start": 21,
        "end": 25,
        "new_start": 37,
        "new_end": 54,
        "label": "DATE_TIME",
        "text": "2018",
        "score": 0.9,
        "language": "en",
        "new_text": "[DATE_TIME_DnuC1]"
    }
    [NAME_GIVEN_dySb5] [NAME_FAMILY_7w4Db3] is a person
    {
        "start": 0,
        "end": 4,
        "new_start": 0,
        "new_end": 18,
        "label": "NAME_GIVEN",
        "text": "John",
        "score": 0.9,
        "language": "en",
        "new_text": "[NAME_GIVEN_dySb5]"
    }
    {
        "start": 5,
        "end": 10,
        "new_start": 19,
        "new_end": 39,
        "label": "NAME_FAMILY",
        "text": "Smith",
        "score": 0.9,
        "language": "en",
        "new_text": "[NAME_FAMILY_7w4Db3]"
    }


.. _record-api-call-section:

Recording API requests
----------------------
When you use the :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` method to redact text, you can optionally record these requests to view and analyze later in the Textual application. The `redact` method takes an optional `record_options` (:class:`RecordApiRequestOptions<tonic_textual.classes.record_api_request_options.RecordApiRequestOptions>`) argument. To record an API request:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.classes.record_api_request_options import RecordApiRequestOptions

    ner = TextualNer()

    ner.redact("My name is John Doe", record_options=RecordApiRequestOptions(
        record=True,
        retention_time_in_hours=1,
        tags=["my_first_request"])
    )

The above code runs the redaction in the same way as any other redaction request, and then records the API request and its results. The request itself is automatically purged after 1 hour.  You can view the results from the **API Explorer** page in Textual.  The retention time is specified in hours and can be set to a value between 1 and 720.


Replacing values in your redaction response
-------------------------------------------

Tonic Textual includes additional utilities for customizing responses.  The :class:`ReplaceTextHelper<tonic_textual.helpers.replace_text_helper.ReplaceTextHelper>` can take a redaction response from our redact call and modify the replacement values.

For example, the below example will modify the replacement values for first names and cities and replace them with equal length strings comprised of just 'x'.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer, Replacement
    from tonic_textual.helpers.replace_text_helper import ReplaceTextHelper
    from typing import Callable, Dict

    ner = TextualNer()
    response = ner.redact("My name is Adam Kamor. I live in Atlanta, GA.")

    replace_funcs: Dict[str, Callable[[Replacement], str]] = {
        'NAME_GIVEN': lambda replacement: 'x'*len(replacement.text),
        'LOCATION_CITY': lambda replacement: 'x'*len(replacement.new_text)
    }

    replacement_helper = ReplaceTextHelper()
    replaced_text = replacement_helper.replace(response, replace_funcs)

