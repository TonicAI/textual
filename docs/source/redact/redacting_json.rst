Redact JSON data
===================
To redact sensitive information from a JSON string or Python dict, pass the object to the `redact_json` method:

Like other SDK functions that modify data the `redact_html` allows you to configure how different entity types are treated.  You can learn more about the common parameters:

* generator_default
* generator_config
* label_allow_lists
* label_block_lists

by reading :ref:`redact-config`.

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

Conversation data stored in JSON
--------------------------------

When conversation data (typically text transcribed from audio recordings) is stored in JSON it is common for different parts of the conversation are found spread across multiple locations in JSON.  Using the redact_json method is not ideal because each piece of text is treated independently when performing NER identification.  This can result in worse NER identification.  The :class:`JsonConversationHelper<tonic_textual.helpers.json_conversation_helper.JsonConversationHelper>` will process entire conversations in single NER calls yielding better performance and then return an NER result that still maps to your original JSON structure.

As an example, let's say you have a JSON document representing a conversation as follows:

.. literalinclude:: json_conversation_example.json
  :language: JSON

Naively, we could process each speech utterance using our redact_json endpoint but we could lose context since each utterance would be run through our models independetly.  Let's use the :class:`JsonConversationHelper<tonic_textual.helpers.json_conversation_helper.JsonConversationHelper>` to improve our results.

.. code-block:: python

    from tonic_textual.redact_api import TextualNer
    from tonic_textual.helpers.json_conversation_helper import JsonConversationHelper

    helper = JsonConversationHelper()
    ner = TextualNer()

    data = {
        "conversation": {
            "transcript": [
                {"speaker": "speaker1", "content": "Hey Adam, it's great to meet you."},
                {"speaker": "speaker2", "content": "Thanks John, great to meet you as well.  Where are you calling in from?"},
                {"speaker": "speaker1", "content": "I'm calling in from Atlanta.  Are we ready to get started or are we waiting on more folks from Tonic to join?"},
                {"speaker": "speaker2", "content": "I think we can get going.  I was hoping Ian would be here but he must be running late."},
                {"speaker": "speaker1", "content": "Sounds good.  Let me get my screen shared and we can get going."}
            ]
        }
    }

    response = helper.redact(data, lambda x: x["conversation"]["transcript"], lambda x: x["content"], lambda content: ner.redact(content))

This yields the following redaction result below.  Each piece of speech from the conversation is stored in its own element in the resulting array.  The order of text in the response matches the order of text in the original conversation.

.. literalinclude:: json_conversation_response.json
  :language: JSON    