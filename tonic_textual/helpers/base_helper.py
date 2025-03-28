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
                    # For multi-line entities, always use the full entity text and replacement
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
        # For other cases, use a proper text replacement algorithm that works with the redacted text
        original_text = redaction_response.original_text
        redacted_text = redaction_response.redacted_text
        redacted_lines = []
        
        # Extract redacted lines directly from the API response 
        # This is the most reliable source of what the redacted text should be
        if "\n" in original_text and "\n" in redacted_text:
            # Simple case: split by newline
            original_lines = original_text.split("\n")
            redacted_lines = redacted_text.split("\n")
            
            # Make sure we have the right number of lines
            if len(original_lines) == len(start_and_ends) and len(redacted_lines) == len(start_and_ends):
                return redacted_lines
        
        # Map entity replacements for each line
        # We'll construct a redacted version of each line by applying the appropriate replacements
        line_replacements = {}
        for line_idx, (line_start, line_end) in enumerate(start_and_ends):
            line_replacements[line_idx] = []
        
        # For each entity, determine which line(s) it affects
        for entity in redaction_response.de_identify_results:
            entity_start = entity['start']
            entity_end = entity['end']
            entity_text = entity['text']
            entity_new_text = entity['new_text']
            
            # Is this a multi-line entity?
            multi_line = False
            affected_lines = []
            
            for line_idx, (line_start, line_end) in enumerate(start_and_ends):
                if entity_start < line_end and entity_end > line_start:
                    affected_lines.append(line_idx)
                    
            # If entity spans multiple lines
            if len(affected_lines) > 1:
                multi_line = True
                
                # Figure out what part of the entity is in each affected line
                for line_idx in affected_lines:
                    line_start, line_end = start_and_ends[line_idx]
                    orig_line = original_text[line_start:line_end]
                    
                    # Is this the first line containing the entity?
                    if line_idx == affected_lines[0]:
                        # First line: from entity start to end of line
                        line_entity_start = entity_start - line_start
                        line_entity_end = len(orig_line)
                        line_entity_text = orig_line[line_entity_start:]
                        
                        # Replace this part with the full replacement
                        line_replacements[line_idx].append({
                            'start': line_entity_start,
                            'end': line_entity_end,
                            'text': line_entity_text,
                            'replacement': entity_new_text
                        })
                    
                    # Is this the last line containing the entity?
                    elif line_idx == affected_lines[-1]:
                        # Last line: from start of line to entity end
                        line_entity_start = 0
                        line_entity_end = entity_end - line_start
                        line_entity_text = orig_line[:line_entity_end]
                        
                        # Replace this part with the full replacement
                        line_replacements[line_idx].append({
                            'start': line_entity_start,
                            'end': line_entity_end,
                            'text': line_entity_text,
                            'replacement': entity_new_text
                        })
                    
                    # Middle line (complete replacement)
                    else:
                        # Middle line: replace entire line
                        line_replacements[line_idx].append({
                            'start': 0,
                            'end': len(orig_line),
                            'text': orig_line,
                            'replacement': entity_new_text
                        })
            
            # Single line entity (simpler case)
            else:
                line_idx = affected_lines[0]
                line_start, line_end = start_and_ends[line_idx]
                
                # Get the line text
                orig_line = original_text[line_start:line_end]
                
                # Calculate positions within the line
                rel_start = entity_start - line_start
                rel_end = entity_end - line_start
                
                # Add replacement info
                line_replacements[line_idx].append({
                    'start': rel_start,
                    'end': rel_end,
                    'text': entity_text,
                    'replacement': entity_new_text
                })
        
        # Apply replacements to each line
        for line_idx, (line_start, line_end) in enumerate(start_and_ends):
            # Get original line text
            orig_line = original_text[line_start:line_end]
            
            # No replacements for this line
            if line_idx not in line_replacements or not line_replacements[line_idx]:
                redacted_lines.append(orig_line)
                continue
            
            # Sort replacements by start position (to handle them in order)
            replacements = sorted(line_replacements[line_idx], key=lambda x: x['start'])
            
            # Apply replacements
            result = orig_line
            offset = 0  # Track position changes due to replacements
            
            for rep in replacements:
                start = rep['start']
                end = rep['end']
                text = rep['text']
                replacement = rep['replacement']
                
                # Apply the replacement
                adjusted_start = start + offset
                adjusted_end = end + offset
                
                # Replace the text
                result = result[:adjusted_start] + replacement + result[adjusted_end:]
                
                # Update offset for next replacement
                offset += len(replacement) - (end - start)
            
            # Add to redacted lines
            redacted_lines.append(result)
        
        return redacted_lines