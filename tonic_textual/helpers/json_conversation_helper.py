from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import (
    RedactionResponse,
)
from typing import Callable, Any, Dict, List, Optional, Tuple


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

    def redact(
        self,
        conversation: dict,
        items_getter: Callable[[dict], list],
        text_getter: Callable[[Any], list],
        redact_func: Callable[[str], RedactionResponse],
        join_char: Optional[str] = '\n',
    ) -> List[RedactionResponse]:
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
        full_text = join_char.join(text_list)

        redaction_response = redact_func(full_text)

        starts_and_ends_original = self.__get_start_and_ends(text_list)
        redacted_lines = self.__get_redacted_lines(
            redaction_response, starts_and_ends_original
        )
        starts_and_ends_redacted = self.__get_start_and_ends(redacted_lines)
        offset_entities = self.__offset_entities(
            redaction_response, starts_and_ends_original, starts_and_ends_redacted
        )

        # start and end of each redacted line. This is needed to update the new_start/new_end in each replacement.

        response = []
        for idx, text in enumerate(text_list):
            response.append(
                RedactionResponse(
                    text, redacted_lines[idx], -1, offset_entities.get(idx, [])
                )
            )

        return response

    """
    Returns a list of tuples. Each tuple contains the start and end position of a given piece of text in the now full text transcript we create.
    If the conversation is represented as:
    {
        "conversations": [
            {"role":"customer", "text": "Hi, this is Adam"},
            {"role":"agent", "text": "Hi Adam, nice to meet you this is Jane."},
        ]
    }  
    Then the list we return would have two tuples.  The first would be (0, 16) and the second from (17, 39)
    """

    @staticmethod
    def __get_start_and_ends(text_list: List[str]) -> List[Tuple[int, int]]:
        start_and_ends = []
        acc = 0
        for text in text_list:
            start_and_ends.append((acc, acc + len(text)))
            acc = acc + len(text) + 1
        return start_and_ends

    """
    Takes the list of entities returned by passing the entire conversation as a single piece of text and offsets the start/end positions to be relative to entities location in the singular piece of text in the JSON.

    If the conversation is represented by:
    {
        "conversations": [
            {"role":"customer", "text": "Hi, this is Adam"},
            {"role":"agent", "text": "Hi Adam, nice to meet you this is Jane."},
        ]
    }  

    Then the entity the text sent to Textual would be  

    Hi, this is Adam
    Hi Adam, nice to meet you this is Jane.

    The first entity response would be for 'Adam' on line 1. We don't need to shift anything. 
    The second and third entities are on line 2.  'Adam' should have a start position of 3 but in fact it is 19 since the Textual response is relative to the start of the entire conversation.  The below code offsets to fix this.
    It also adds a new property to the entity called 'idx' which corresponds to which item in the conversational array the entity belongs.
    
    """

    @staticmethod
    def __offset_entities(
        redaction_response: RedactionResponse,
        start_and_ends_original: List[Tuple[int, int]],
        start_and_ends_redacted: List[Tuple[int, int]],
    ) -> Dict[int, List[Replacement]]:
        offset_entities = dict()

        for entity in redaction_response["de_identify_results"]:
            offset = 0
            redacted_offset = 0
            arr_idx = 0
            # find which start_and_end the entity is in, like finding the index of the conversation item in which the entity belongs
            for start_and_end in start_and_ends_original:
                if entity["start"] <= start_and_end[1]:
                    offset = start_and_end[0]
                    break
                arr_idx = arr_idx + 1

            for start_and_end_redacted in start_and_ends_redacted:
                if entity["new_start"] <= start_and_end_redacted[1]:
                    redacted_offset = start_and_end_redacted[0]
                    break

            offset_entity = Replacement(
                entity["start"] - offset,
                entity["end"] - offset,
                entity["new_start"] - redacted_offset,
                entity["new_end"] - redacted_offset,
                entity["label"],
                entity["text"],
                entity["score"],
                entity["language"],
                entity["new_text"],
                None,
                None,
                None,
            )

            if arr_idx in offset_entities:
                offset_entities[arr_idx].append(offset_entity)
            else:
                offset_entities[arr_idx] = []
                offset_entities[arr_idx].append(offset_entity)

        return offset_entities

    """
    Computes the length difference between an original piece of text and a redacted/synthesized piece of text
    """

    @staticmethod
    def __get_line_length_difference(
        idx: int,
        start_and_ends: List[Tuple[int, int]],
        redaction_response: RedactionResponse,
    ) -> int:
        start = start_and_ends[idx][0]
        end = start_and_ends[idx][1]

        entities = list(
            filter(
                lambda x: x.start >= start and x.end <= end,
                redaction_response.de_identify_results,
            )
        )
        acc = 0
        for entity in entities:
            acc = acc + (len(entity["new_text"]) - len(entity["text"]))
        return acc

    """
    Grabs substrings from the redacted_text property of the Textual RedactionResponse.
    """

    @staticmethod
    def __get_redacted_lines(
        redaction_response: RedactionResponse, start_and_ends: List[Tuple[int, int]]
    ) -> List[str]:
        offset = 0
        redacted_lines = []
        for idx in range(len(start_and_ends)):
            length_difference = JsonConversationHelper.__get_line_length_difference(
                idx, start_and_ends, redaction_response
            )

            start = start_and_ends[idx][0]
            end = start_and_ends[idx][1]
            redacted_line = redaction_response.redacted_text[
                (start + offset) : (end + offset + length_difference)
            ]
            offset = offset + length_difference
            redacted_lines.append(redacted_line)
        return redacted_lines
