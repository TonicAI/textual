
Conversation data stored in JSON
--------------------------------

When conversation data (typically text transcribed from audio recordings) is stored in JSON typically different parts of the conversation are found spread across multiple locations in JSON.  Using the redact_json method is not ideal because each piece of text is treated independently when performing NER identification.  This can result in worse NER identification.  The :class:`JsonConversationHelper<tonic_textual.helpers.json_conversation_helper.JsonConversationHelper>` will process entire conversations in single NER calls yielding better performance and then return an NER result that still maps to your original JSON structure.

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