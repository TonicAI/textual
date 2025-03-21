from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from typing import Callable, Dict

class ReplaceTextHelper:
    """
    A helper class for modifying synthetic values returned from redaction calls
    """
    def __init__(self):
        pass

    def replace(self, redaction_response: RedactionResponse, replace_funcs: Dict[str, Callable[[str, str], str]])->str:
        swaps = []
        for pii_type, func in replace_funcs.items():
            replacements = list(filter(lambda x: x.label==pii_type, redaction_response.de_identify_results))            
            for replacement in replacements:
                replaced_value = func(replacement)
                swaps.append((replaced_value, replacement.new_start, replacement.new_end))

            
        return self.__replace_multiple_ranges(redaction_response.redacted_text, swaps)


    def __replace_multiple_ranges(self, s, replacements):
        """
        Replace multiple ranges in the string `s`. Each replacement is specified
        as a tuple: (replacement_value, start_index, end_index), where the range is
        inclusive. Replacements are applied in reverse order to preserve indices.

        Args:
            s (str): The original string.
            replacements (list of tuples): Each tuple contains:
                - replacement (str): The new value to insert.
                - start_index (int): The starting index of the range to remove.
                - end_index (int): The ending index of the range to remove (inclusive).

        Returns:
            str: The modified string with all specified ranges replaced.
        """
        # Sort the replacements by start_index in descending order.
        for replacement, start_index, end_index in sorted(replacements, key=lambda x: x[1], reverse=True):
            s = s[:start_index] + replacement + s[end_index:]
        return s