🚀 Getting started
=====================

Install the Tonic Textual SDK
-----------------------------
Before you get started, you must install the Textual Python SDK:

.. code-block:: python

    pip install tonic-textual

Set up a Textual API key
------------------------
To authenticate with Tonic Textual, you must set up an API key.  You can obtain an API key from the **User API Keys** page in Tonic Textual after |signup_link|.

After, you obtain the key, you can optionally set it as an environment variable:

.. code-block:: bash

    export TONIC_TEXTUAL_API_KEY="<API-KEY>""

You can can also pass the API key as a parameter when you initialize the TonicTextual object:

.. code-block:: python

    from tonic_textual.redact_api import TextualNer

    textual = TonicTextual("<TONIC-TEXTUAL-URL>", api_key="<API-KEY>")


.. |signup_link| raw:: html

   <a href="https://textual.tonic.ai/signup" target="_blank">creating your account</a>