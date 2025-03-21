from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from tonic_textual.helpers.base_helper import BaseHelper
from typing import Callable, Any, List

class JsonConversationHelper:
    """A helper class for processing generic chat data and transcripted audio where the conversation is broken down into pieces and represented in JSON.  For example, 
    {
        \"conversations\": [
            {\"role\":\"customer\", \"text\": \"Hi, this is Adam\"},
            {\"role\":\"agent\", \"text\": \"Hi Adam, nice to meet you this is Jane.\"},
        ]
    }    
    """
    
    def __init__(self):
        pass

    def redact(self, conversation: dict, items_getter: Callable[[dict], list], text_getter: Callable[[Any], list], redact_func: Callable[[str], RedactionResponse]) -> List[RedactionResponse]:
        """Redacts a conversation.

        Parameters
        ----------
        conversation: dict
            The python dictionary, loaded from JSON, which contains the text parts of the conversation

        items_getter: Callable[[dict], list]
            A function that can retrieve the array of conversation items. e.g. if conversation is represented in JSON as:
            {
                "conversations": [
                    {"role":"customer", "text": "Hi, this is Adam"},
                    {"role":"agent", "text": "Hi Adam, nice to meet you this is Jane."},
                ]
            }  

            Then items_getter would be defined as lambda x: x["conversations]

        text_getter: Callable[[dict], str]
            A function to retrieve the text from a given item returned by the items_getter.  For example, if the items_getter returns a list of objects such as:
            
            {"role":"customer", "text": "Hi, this is Adam"}

            Then the items_getter would be defined as lambda x: x["text"]

        redact_func: Callable[[str], RedactionResponse]
            The function you use to make the Textual redaction call.  This should be an invocation of the TextualNer.redact such as lambda x: ner.redact(x).
        """

        items = items_getter(conversation)
        text_list = [text_getter(item) for item in items]
        full_text = '\n'.join(text_list)

        redaction_response = redact_func(full_text)

        starts_and_ends_original = BaseHelper.get_start_and_ends(text_list)                
        redacted_lines = BaseHelper.get_redacted_lines(redaction_response, starts_and_ends_original)
        starts_and_ends_redacted = BaseHelper.get_start_and_ends(redacted_lines)
        offset_entities = BaseHelper.offset_entities(redaction_response, starts_and_ends_original, starts_and_ends_redacted)
        

        # start and end of each redacted line. This is needed to update the new_start/new_end in each replacement.
        


        response = []
        for idx, text in enumerate(text_list):
            response.append(RedactionResponse(text, redacted_lines[idx], -1, offset_entities.get(idx,[])))

        return response
    