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
        """
        Handle entities that span multiple lines by mapping them to their appropriate line positions.
        For entities that cross line boundaries, this creates multiple Replacement objects, one for each line
        that the entity spans across. Each replacement uses the complete entity text and replacement.
        """
        offset_entities = dict()
        
        # Get the original text and redacted text
        original_text = redaction_response.original_text
        
        # Process each entity
        for entity in redaction_response['de_identify_results']:
            entity_start = entity['start']
            entity_end = entity['end']
            entity_text = entity['text']
            entity_new_text = entity['new_text']
            
            # Find which lines this entity spans across
            lines_spanned = []
            for idx, (start, end) in enumerate(start_and_ends_original):
                if entity_start < end and entity_end > start:
                    lines_spanned.append(idx)
            
            # For multi-line entities, special handling is needed
            if len(lines_spanned) > 1:
                # Create a replacement for each line this entity spans
                for line_idx in lines_spanned:
                    line_start, line_end = start_and_ends_original[line_idx]
                    
                    # Figure out what part of the entity is in this line
                    line_entity_start = max(entity_start, line_start)
                    line_entity_end = min(entity_end, line_end)
                    
                    # Convert to positions relative to line start
                    rel_start = line_entity_start - line_start
                    rel_end = line_entity_end - line_start
                    
                    # Create a replacement for this line
                    line_entity = Replacement(
                        rel_start,
                        rel_end,
                        rel_start,
                        rel_start + len(entity_new_text),
                        entity["label"],
                        entity_text,  # Use the full entity text
                        entity["score"],
                        entity["language"],
                        entity_new_text,  # Use the full replacement text
                        None, None, None
                    )
                    
                    # Add to offset entities
                    if line_idx in offset_entities:
                        offset_entities[line_idx].append(line_entity)
                    else:
                        offset_entities[line_idx] = [line_entity]
            else:
                # Single-line entity - simpler case
                line_idx = lines_spanned[0]
                line_start = start_and_ends_original[line_idx][0]
                
                # Calculate relative positions
                rel_start = entity_start - line_start
                rel_end = entity_end - line_start
                
                # Create the replacement
                line_entity = Replacement(
                    rel_start,
                    rel_end,
                    rel_start,
                    rel_start + len(entity_new_text),
                    entity["label"],
                    entity_text,
                    entity["score"],
                    entity["language"],
                    entity_new_text,
                    None, None, None
                )
                
                # Add to offset entities
                if line_idx in offset_entities:
                    offset_entities[line_idx].append(line_entity)
                else:
                    offset_entities[line_idx] = [line_entity]
        
        return offset_entities

    """
    Computes the length difference between an original piece of text and a redacted/synthesized piece of text
    """
    @staticmethod
    def get_line_length_difference(idx: int, start_and_ends: List[Tuple[int,int]], redaction_response: RedactionResponse) -> int:
        start = start_and_ends[idx][0]
        end = start_and_ends[idx][1]

        entities = []
        for entity in redaction_response.de_identify_results:
            entity_start = entity['start']
            entity_end = entity['end']
            if entity_start < end and entity_end > start:
                entities.append(entity)
                
        acc = 0 
        for entity in entities:
            # For multi-line entities spanning this line, we need special handling
            entity_start = entity['start']
            entity_end = entity['end']
            
            # If this entity spans multiple lines
            if entity_start < start or entity_end > end:
                # For multi-line entities, use the full replacement text
                # minus the length of the original text in this line
                line_overlap_start = max(entity_start, start)
                line_overlap_end = min(entity_end, end)
                original_length = line_overlap_end - line_overlap_start
                new_length = len(entity['new_text'])
                
                acc = acc + (new_length - original_length)
            else:
                # Single line entity - simpler case
                acc = acc + (len(entity['new_text']) - len(entity['text']))
                
        return acc

    """
    Creates redacted lines by directly replacing the entities in each line with their replacement text.
    For multi-line entities, the full replacement text is used on each affected line.
    """
    @staticmethod
    def get_redacted_lines(redaction_response: RedactionResponse, start_and_ends: List[Tuple[int,int]]) -> List[str]:
        """
        Creates redacted lines by replacing entities within each line.
        For multi-line entities, each affected line gets the complete replacement text.
        """
        original_text = redaction_response.original_text
        redacted_lines = []
        
        # Process entities and collect replacements for each line
        replacements_by_line = {}
        for i in range(len(start_and_ends)):
            replacements_by_line[i] = []
            
        # Find which entities affect which lines and at what positions
        for entity in redaction_response.de_identify_results:
            entity_start = entity['start']
            entity_end = entity['end']
            entity_text = entity['text']
            replacement_text = entity['new_text']
            
            # Determine which lines this entity spans
            for line_idx, (line_start, line_end) in enumerate(start_and_ends):
                # If this entity affects this line
                if entity_start < line_end and entity_end > line_start:
                    # Compute the part of the entity that falls in this line
                    start_in_line = max(0, entity_start - line_start)
                    end_in_line = min(line_end - line_start, entity_end - line_start)
                    
                    # Store the replacement details
                    replacements_by_line[line_idx].append({
                        'start': start_in_line,  # Position in the line, not the full text
                        'end': end_in_line,
                        'replacement': replacement_text  # Always use full replacement
                    })
                    
        # Process each line
        for line_idx, (line_start, line_end) in enumerate(start_and_ends):
            line_text = original_text[line_start:line_end]
            line_replacements = sorted(replacements_by_line[line_idx], key=lambda r: r['start'])
            
            # Apply replacements to this line
            result = []
            last_end = 0
            
            for rep in line_replacements:
                # Add text before replacement
                if rep['start'] > last_end:
                    result.append(line_text[last_end:rep['start']])
                
                # Add replacement text
                result.append(rep['replacement'])
                
                # Update position
                last_end = rep['end']
            
            # Add any remaining text
            if last_end < len(line_text):
                result.append(line_text[last_end:])
                
            # Combine into the redacted line and add to results
            redacted_lines.append(''.join(result))
            
        return redacted_lines