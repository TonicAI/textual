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

You can can also pass the API key as a parameter when you create your Textual client.


Creating a Textual client
--------------------------

For performing redaction of text or files, use our TextualNer client.  For parsing files, useful for extracting information for files such as PDF and DOCX use our TextualParse client

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.parse_api import TextualParse
    
    textual = TextualNer()
    textual = TextualParse()

Both client support several optional arguments.

* **base_url** - The URL of the server that hosts Tonic Textual. Defaults to https://textual.tonic.ai

* **api_key** - Your API key. If not specified, you must set TONIC_TEXTUAL_API_KEY in your environment.

* **verify** - Whether to verify SSL certification. Default is true.

.. |signup_link| raw:: html

   <a href="https://textual.tonic.ai/signup" target="_blank">creating your account</a>