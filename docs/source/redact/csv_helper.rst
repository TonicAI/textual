Processing data in CSV files
----------------------------

Typically, in a CSV file you only wish to process a specific column or columns of data.  Additionally, different rows of data might relate to each other, for example if the CSV stored a chat conversation where each row was a single message, but multiple rows together formed a conversation.  This helper class can be used to group rows of data together to yield more accurate identification by maximizing context sent to our NER model.  It can then return either entity information of each row or a new, redacted CSV.

As an example, imagine a CSV with 3 columns.

#. message_id
#. conversation_id
#. message

So this particular CSV can store many messages spread across many conversations.  Ideally, we would want to create a single document matching each conversation prior to processing in order to ensure the best quality identification.  This can be solved with the code below.  This first example returns redaction results for each row and handles the pre-processing transparently.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.helpers.csv_helper import CsvHelper

    helper = CsvHelper()
    ner = TextualNer()

    with open('original.csv', 'r') as f:
        response = helper.redact(f, True, lambda row: row['conversation_id'], lambda row: row['message'], lambda x: ner.redact(x))

The key call here is to the helper's redact method.  This function requires you to pass in several arguments:

* The csv file
* Whether or not the first row should be treated as a header
* A function which shows how to group columns into messages, if not specified we group all rows together
* A function which shows how to retrieve the necessary text
* A function for redacting, this normally is a wrapper around the TextualNer redact() method

You can also create a new redacted file.  The function signature is similar.  Here is an example:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.helpers.csv_helper import CsvHelper

    helper = CsvHelper()
    ner = TextualNer()

    with open('original.csv', 'r') as f:
        buf = helper.redact_and_reconstruct(f, True, 'id', 'text', lambda x: ner.redact(x))

    with open('redacted.csv', mode='w') as f:
        print(buf.getvalue(), file=f)

In this example we write the redacted CSV back to disk.  The function arguments are also slightly different.  They are:

* The csv file
* Whether or not the first row should be treated as a header
* The column used for grouping, if not specified we group all rows together
* The column containing the text
* A function for redacting, this normally is a wrapper around the TextualNer redact() method