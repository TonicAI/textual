Redact raw text
---------------
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

Redact JSON data
----------------
To redact sensitive information from a JSON string or Python dict, pass the object to the `redact_json` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import json

    textual = TextualNer()

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

Redact HTML data
----------------
To redact sensitive information from HTML, pass the HTML document string to the `redact_html` method:

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

Choosing tokenization or synthesis  raw text
----------------------------------------------
You can choose whether to synthesize or tokenize a given entity. By default, all entities are tokenized.

To specify the entities to synthesize or tokenize, use the `generator_config` parameter. This works the same way for all of the `redact` functions.

The following example passes a string to the `redact` method, but sets some entities to `Synthesis`, which indicates to use realistic replacement values:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()
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
The following example passes the string to the `llm_synthesis` method:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TextualNer()

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

Note that LLM Synthesis is non-deterministic — you will likely get different results each time you run it.


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


Working with DataFrames
--------------------------------------

The :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` function can be called as a user-defined function (UDF) on a DataFrame column.  As an example, lets read a CSV file redact a given column, and write the CSV back to disk.  Make sure to first install pandas.

.. code-block:: bash
    
    pip install pandas

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import pandas as pd

    ner = TextualNer()

    df = pd.read_csv('file.csv')

    # Let's say there is a notes column in the CSV containing unstructured text
    df['notes'] = df['notes'].apply(lambda x: ner.redact(x).redacted_text if not pd.isnull(x) else None))

    df.to_csv('file_redacted.csv')

Working with large data sets
-----------------------------

For most use cases the :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` and :meth:`redact<tonic_textual.redact_api.TextualNer.redact_bulk>` functions are sufficient.  However, sometimes you need to process a lot of data quickly.  Typically this means making multiple redact requests concurrently instead of sequentially.

We can accomplish this using Python's asyncio library which you can install below.

.. code-block:: bash

    pip install asyncio

The below snippet can be used to process a large number of files through concurrent requests.  **Note that this snippet will not run in in a Jupyter notebook due to how Jupyter notebook handles event loops.  Below is a second example when running in Jupypter notebook**

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import asyncio

    ner = TextualNer()

    file_names = ['...'] # The list of files to be processed asynchronously


    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, ner.redact, open(file,'r').read()) for file in file_names]
    loop.run_until_complete(asyncio.gather(*tasks))

    results = [task.result() for task in tasks]

If you run the above and see an error like **The event loop is already running** this is likely because you are running in a Jupyter notebook.  To successfully run in a Jupyter notebook please use the following:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import asyncio

    ner = TextualNer()

    file_names = ['...'] # The list of files to be processed asynchronously

    async def async_redact(t):
        return  ner.redact(t)

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(async_redact(open(file,'r').read())) for file in file_names]
    await asyncio.gather(*tasks)

    results = [task.result() for task in tasks]

In another case, perhaps you are processing DataFrames but the frames themselves are quite large and you wish to redact rows in parallel.  For this we can use Dask, a framework that sits on top of Pandas for concurrent execution.  Make sure to first install dask[dataframe] and pandas.

.. code-block:: bash

    pip install pandas
    pip install dask[dataframe]

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import pandas as pd
    import dask.dataframe as dd

    # Load your DataFrame from disk, a live DB connection, etc.
    df = get_dataframe()

    npartitions=25 # Sets the number of requests to make concurrently.
    df[col] = dd.from_pandas(df[col], npartitions=npartitions).apply(lambda x: redact(x) if not pd.isnull(x) else x, meta=pd.Series(dtype='str', name=col)).compute()

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

