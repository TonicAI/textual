from typing import List, Tuple, Dict

from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse


class BaseHelper(object):
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
    def get_start_and_ends(text_list: List[str]) -> List[Tuple[int,int]]:
        start_and_ends = []
        acc = 0
        for text in text_list:
            start_and_ends.append((acc, acc+len(text)))
            acc=acc+len(text) + 1
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
    def offset_entities(redaction_response: RedactionResponse, start_and_ends_original: List[Tuple[int,int]], start_and_ends_redacted: List[Tuple[int,int]]) -> Dict[int, List[Replacement]]:
        offset_entities = dict()

        for entity in redaction_response['de_identify_results']:            
            # Track all line indices that this entity spans
            entity_start = entity['start']
            entity_end = entity['end']
            entity_new_start = entity['new_start']
            entity_new_end = entity['new_end']
            
            # Find all line indices this entity spans
            for arr_idx, (start, end) in enumerate(start_and_ends_original):
                # Check if entity overlaps with this line
                if (entity_start <= end and entity_end > start):
                    # Calculate offsets for this line
                    offset = start
                    
                    # Find matching redacted offset
                    redacted_offset = 0
                    for redacted_start, redacted_end in start_and_ends_redacted:
                        if arr_idx < len(start_and_ends_redacted) and redacted_start == start_and_ends_redacted[arr_idx][0]:
                            redacted_offset = redacted_start
                            break
                    
                    # Calculate line-specific start and end positions
                    line_entity_start = max(entity_start, start) - offset
                    line_entity_end = min(entity_end, end) - offset
                    
                    # Calculate redacted text offsets for this line
                    line_entity_new_start = max(entity_new_start, redacted_offset) - redacted_offset
                    line_entity_new_end = min(entity_new_end, start_and_ends_redacted[arr_idx][1]) - redacted_offset
                    
                    # Create a line-specific entity
                    offset_entity = Replacement(
                        line_entity_start,
                        line_entity_end,
                        line_entity_new_start,
                        line_entity_new_end,
                        entity["label"],
                        entity["text"],
                        entity["score"],
                        entity["language"],
                        entity["new_text"],
                        None,
                        None,
                        None
                    )
                    
                    # Add to the appropriate line index
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
    def get_line_length_difference(idx: int, start_and_ends: List[Tuple[int,int]], redaction_response: RedactionResponse) -> int:
        start = start_and_ends[idx][0]
        end = start_and_ends[idx][1]

        entities = list(filter(lambda x: x.start>=start and x.end<=end, redaction_response.de_identify_results))
        acc = 0 
        for entity in entities:
            acc = acc + (len(entity['new_text'])-len(entity['text']))
        return acc

    """
    Grabs substrings from the redacted_text property of the Textual RedactionResponse.
    """
    @staticmethod
    def get_redacted_lines(redaction_response: RedactionResponse, start_and_ends: List[Tuple[int,int]]) -> List[str]:
        offset = 0
        redacted_lines=[]
        for idx in range(len(start_and_ends)):
            length_difference = BaseHelper.get_line_length_difference(idx, start_and_ends, redaction_response)

            start = start_and_ends[idx][0]
            end = start_and_ends[idx][1]
            redacted_line = redaction_response.redacted_text[(start+offset):(end+offset+length_difference)]
            offset = offset + length_difference
            redacted_lines.append(redacted_line)
        return redacted_lines