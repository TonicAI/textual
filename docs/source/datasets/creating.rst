Creating a dataset
======================

To create a dataset:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    
    textual = TextualNer()
    
    dataset = textual.create_dataset('my_dataset')