Redact JSON data
===================

Using redact_json
-----------------

To redact sensitive information from a JSON string or Python dict, pass the object to the ``redact_json`` method:

Similar to other SDK functions that modify data, ``redact_html`` allows you to configure how to treat different entity types.

To learn more about the common parameters:

* ``generator_default``
* ``generator_config``
* ``label_allow_lists``
* ``label_block_lists``

go to :ref:`redact-config`.

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

When conversation data, such as text transcribed from audio recordings is stored in JSON, different parts of the conversation are often spread across multiple locations in JSON.

Using ``redact_json`` method is not ideal in this case, because NER identification treats each piece of text independently. This can result in worse NER identification.

The :class:`JsonConversationHelper<tonic_textual.helpers.json_conversation_helper.JsonConversationHelper>` processes entire conversations in single NER calls, which improves performance, and then returns an NER result that still maps to your original JSON structure.

For example, the following JSON document represents a conversation:

.. literalinclude:: json_conversation_example.json
  :language: JSON

Naively, we could use the ``redact_json`` endpoint to process each speech utterance. However, we might lose context, because each utterance runs through our models independetly.

To improve the results, we'll use the :class:`JsonConversationHelper<tonic_textual.helpers.json_conversation_helper.JsonConversationHelper>`.

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

This produces the following redaction result. In the resulting array, each piece of speech from the conversation is stored in its own element. The order of the text in the response matches the order of text in the original conversation.

.. literalinclude:: json_conversation_response.json
  :language: JSON    
