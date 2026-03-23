Working with DataFrames
=========================

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