Working with DataFrames
=========================

The :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` function can be called as a user-defined function (UDF) on a DataFrame column.

Before you do this, you must install pandas.

.. code-block:: bash
    
    pip install pandas

The following example:

1. Reads a CSV file.

2. Redacts a given column.

3. Writes the CSV back to disk.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import pandas as pd

    ner = TextualNer()

    df = pd.read_csv('file.csv')

    # Let's say there is a notes column in the CSV containing unstructured text
    df['notes'] = df['notes'].apply(lambda x: ner.redact(x).redacted_text if not pd.isnull(x) else None))

    df.to_csv('file_redacted.csv')
