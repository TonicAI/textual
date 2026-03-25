Processing data in CSV files
============================

Typically, in a CSV file you only want to process a specific column or columns of data.

Also, different rows of data might relate to each other. For example, a CSV stores a chat conversation where each row is a single message, but multiple rows together form a conversation.

You can use this helper class to group rows of data to yield more accurate identification by maximizing the context that you send to our NER model.

It can then return either the entity information for each row or a new, redacted CSV.

For example, a CSV file contains the following columns:

#. message_id
#. conversation_id
#. message

This CSV file stores many messages spread across many conversations.

Creating a single document to group the conversations
-----------------------------------------------------

Before processing, to ensure the best quality detections, we create a single document that matches each conversation.

This can be solved with the code below. This example returns redaction results for each row and handles the pre-processing transparently.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.helpers.csv_helper import CsvHelper

    helper = CsvHelper()
    ner = TextualNer()

    with open('original.csv', 'r') as f:
        response = helper.redact(f, True, lambda row: row['conversation_id'], lambda row: row['message'], lambda x: ner.redact(x))

The key call here is to the helper's ``redact`` method. This function requires you to pass in the following arguments:

* The CSV file.
* Whether to treat the first row as a header.
* A function that shows how to group columns into messages. If not specified all rows are grouped together.
* A function that shows how to retrieve the necessary text.
* A function for redacting. This is normally a wrapper around the TextualNer ``redact()`` method.

Creating a new redacted CSV file
-----------------------------------------------------

You can also create a new redacted file. The following example writes the redacted CSV back to disk:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.helpers.csv_helper import CsvHelper

    helper = CsvHelper()
    ner = TextualNer()

    with open('original.csv', 'r') as f:
        buf = helper.redact_and_reconstruct(f, True, 'id', 'text', lambda x: ner.redact(x))

    with open('redacted.csv', mode='w') as f:
        print(buf.getvalue(), file=f)

The function arguments to create a redacted file are slightly different:

* The CSV file.
* Whether to treat the first row as a header
* The column used for grouping. If not specified, all rows are grouped together.
* The column that contains the text.
* A function to use to redact the file. This normally is a wrapper around the TextualNer ``redact()`` method.
