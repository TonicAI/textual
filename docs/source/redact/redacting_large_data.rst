Working with large data sets
=================================

For most use cases, the :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` and :meth:`redact_bulk<tonic_textual.redact_api.TextualNer.redact_bulk>` functions are sufficient.

However, sometimes you need to process a lot of data quickly. Typically, this means making multiple redact requests concurrently instead of sequentially.

To accomplish this, you can use Python's asyncio library. To install asyncio:

.. code-block:: bash

    pip install asyncio

Issuing concurrent requests
---------------------------

The below snippet can be used to process a large number of files through concurrent requests.

**Note that because of how Jupyter notebook handles event loops, this snippet cannot run in in a Jupyter notebook. A later example shows how to run in Jupypter notebook.**

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import asyncio

    ner = TextualNer()

    file_names = ['...'] # The list of files to be processed asynchronously


    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, ner.redact, open(file,'r').read()) for file in file_names]
    loop.run_until_complete(asyncio.gather(*tasks))

    results = [task.result() for task in tasks]

Running in a Jupyter notebook
-----------------------------
If you run the above and see an error similar to **The event loop is already running**, this is likely because you are running in a Jupyter notebook.

To successfully run in a Jupyter notebook, use the following:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    import asyncio

    ner = TextualNer()

    file_names = ['...'] # The list of files to process asynchronously

    async def async_redact(t):
        return  ner.redact(t)

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(async_redact(open(file,'r').read())) for file in file_names]
    await asyncio.gather(*tasks)

    results = [task.result() for task in tasks]

Processing large DataFrames
---------------------------

In another case, you might be processing very large DataFrame, and want to redact rows in parallel.

For this we can use Dask, a framework that sits on top of Pandas for concurrent execution.

Before you use Dask, you must install dask[dataframe] and pandas.

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
