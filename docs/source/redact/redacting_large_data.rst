Working with large data sets
=================================

For most use cases the :meth:`redact<tonic_textual.redact_api.TextualNer.redact>` and :meth:`redact_bulk<tonic_textual.redact_api.TextualNer.redact_bulk>` functions are sufficient.  However, sometimes you need to process a lot of data quickly.  Typically this means making multiple redact requests concurrently instead of sequentially.

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