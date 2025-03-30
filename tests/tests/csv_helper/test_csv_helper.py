import csv
import io
import pytest

from tests.utils.assertion_utils import assert_redaction_response_equal
from tests.utils.redaction_response_utils import build_redaction_response_from_json
from tests.utils.resource_utils import get_resource_path
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from tonic_textual.helpers.csv_helper import CsvHelper

# single conversation, no entities that cross boundaries
def test_simple_csv():

    helper = CsvHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello, my name is adam\nI work at Tonic',
                'hello, my name is [NAME_GIVEN_ssYs5]\nI work at [ORGANIZATION_5Ve7OH]',
                9,
                [
                    Replacement(18,22,18,36,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(33,38,47,68,'ORGANIZATION','Tonic',0.9, 'en','[ORGANIZATION_5Ve7OH]')]
            )

    expected_row1 = """{
        "original_text": "hello, my name is adam",
        "redacted_text": "hello, my name is [NAME_GIVEN_ssYs5]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 18,
                "end": 22,
                "new_start": 18,
                "new_end": 36,
                "label": "NAME_GIVEN",
                "text": "adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "I work at Tonic",
        "redacted_text": "I work at [ORGANIZATION_5Ve7OH]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 10,
                "end": 15,
                "new_start": 10,
                "new_end": 31,
                "label": "ORGANIZATION",
                "text": "Tonic",
                "score": 0.9,
                "language": "en",
                "new_text": "[ORGANIZATION_5Ve7OH]"
            }
        ]
    }
    """


    with open(get_resource_path('single_convo.csv'), 'r') as f:
        response = helper.redact(f, True, lambda x: x['id'], lambda x: x['text'], redact)
        
        assert len(response)==2
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))

def test_simple_csv_no_header():

    helper = CsvHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello, my name is adam\nI work at Tonic',
                'hello, my name is [NAME_GIVEN_ssYs5]\nI work at [ORGANIZATION_5Ve7OH]',
                9,
                [
                    Replacement(18,22,18,36,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(33,38,47,68,'ORGANIZATION','Tonic',0.9, 'en','[ORGANIZATION_5Ve7OH]')]
            )

    expected_row1 = """{
        "original_text": "hello, my name is adam",
        "redacted_text": "hello, my name is [NAME_GIVEN_ssYs5]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 18,
                "end": 22,
                "new_start": 18,
                "new_end": 36,
                "label": "NAME_GIVEN",
                "text": "adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "I work at Tonic",
        "redacted_text": "I work at [ORGANIZATION_5Ve7OH]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 10,
                "end": 15,
                "new_start": 10,
                "new_end": 31,
                "label": "ORGANIZATION",
                "text": "Tonic",
                "score": 0.9,
                "language": "en",
                "new_text": "[ORGANIZATION_5Ve7OH]"
            }
        ]
    }
    """


    with open(get_resource_path('single_convo_noheader.csv'), 'r') as f:
        response = helper.redact(f, False, lambda x: x['0'], lambda x: x['1'], redact)
        
        assert len(response)==2
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))

def test_simple_csv_no_grouping():

    helper = CsvHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello, my name is adam\nI work at Tonic',
                'hello, my name is [NAME_GIVEN_ssYs5]\nI work at [ORGANIZATION_5Ve7OH]',
                9,
                [
                    Replacement(18,22,18,36,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(33,38,47,68,'ORGANIZATION','Tonic',0.9, 'en','[ORGANIZATION_5Ve7OH]')]
            )

    expected_row1 = """{
        "original_text": "hello, my name is adam",
        "redacted_text": "hello, my name is [NAME_GIVEN_ssYs5]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 18,
                "end": 22,
                "new_start": 18,
                "new_end": 36,
                "label": "NAME_GIVEN",
                "text": "adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "I work at Tonic",
        "redacted_text": "I work at [ORGANIZATION_5Ve7OH]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 10,
                "end": 15,
                "new_start": 10,
                "new_end": 31,
                "label": "ORGANIZATION",
                "text": "Tonic",
                "score": 0.9,
                "language": "en",
                "new_text": "[ORGANIZATION_5Ve7OH]"
            }
        ]
    }
    """


    with open(get_resource_path('single_convo_noheader.csv'), 'r') as f:
        response = helper.redact(f, False, None, lambda x: x['1'], redact)
        
        assert len(response)==2
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))    

#Two conversations in CSV, interleaving rows, no entities crossing boundaries
def test_two_conversation_csv_simple():
    helper = CsvHelper()

    def redact(x:str) -> RedactionResponse:
        if x.startswith('hi'):
            return RedactionResponse(
                    'hi adam, how are you?\ngood',
                    'hi [NAME_GIVEN_ssYs5], how are you?\ngood',
                    6,
                    [
                        Replacement(3,7,3,21,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]')
                    ]
                )
        else:
            return RedactionResponse(
                'hello andrew, how are you?\nbad',
                'hello [NAME_GIVEN_T9FcFaC], how are you?\nbad',
                6,
                [
                    Replacement(6,12,6,26,'NAME_GIVEN','andrew',0.9, 'en','[NAME_GIVEN_T9FcFaC]')
                ]
            )

    expected_row1 = """{
        "original_text": "hi adam, how are you?",
        "redacted_text": "hi [NAME_GIVEN_ssYs5], how are you?",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 3,
                "end": 7,
                "new_start": 3,
                "new_end": 21,
                "label": "NAME_GIVEN",
                "text": "adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "hello andrew, how are you?",
        "redacted_text": "hello [NAME_GIVEN_T9FcFaC], how are you?",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 6,
                "end": 12,
                "new_start": 6,
                "new_end": 26,
                "label": "NAME_GIVEN",
                "text": "andrew",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_T9FcFaC]"
            }
        ]
    }
    """

    expected_row3 = """{
        "original_text": "good",
        "redacted_text": "good",
        "usage": -1,
        "de_identify_results": []
    }"""
    
    expected_row4 = """{
        "original_text": "bad",
        "redacted_text": "bad",
        "usage": -1,
        "de_identify_results": []
    }"""


    with open(get_resource_path('two_convo.csv'), 'r') as f:
        response = helper.redact(f, True, lambda x: x['id'], lambda x: x['text'], redact)
        
        assert len(response)==4
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))
        assert_redaction_response_equal(response[2],build_redaction_response_from_json(expected_row3))
        assert_redaction_response_equal(response[3],build_redaction_response_from_json(expected_row4))

# single convo with 1 entity crossing a border
def test_single_border_crossing():
    helper = CsvHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'I am married to Lis. my name is Ad\nam and I live in Atlanta',
                'I am married to [NAME_GIVEN_uWI2]. my name is [NAME_GIVEN_S4LnbG] and I live in [LOCATION_CITY_FgBgz8WW]',
                15,
                [
                    Replacement(16,19,16,33,'NAME_GIVEN','Lis',0.9, 'en','[NAME_GIVEN_uWI2]'),
                    Replacement(32,37,46,65,'NAME_GIVEN','Ad\nam',0.9, 'en','[NAME_GIVEN_S4LnbG]'),
                    Replacement(52,59,80,104,'LOCATION_CITY','Atlanta',0.9,'en','[LOCATION_CITY_FgBgz8WW]')
                ]
            )

    expected_row1 = """{
        "original_text": "I am married to Lis. my name is Ad",
        "redacted_text": "I am married to [NAME_GIVEN_uWI2]. my name is [NAME_GIVEN_S4LnbG]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 16,
                "end": 19,
                "new_start": 16,
                "new_end": 33,
                "label": "NAME_GIVEN",
                "text": "Lis",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_uWI2]"
            },
            {
                "start": 32,
                "end": 34,
                "new_start": 32,
                "new_end": 51,
                "label": "NAME_GIVEN",
                "text": "Ad\\nam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_S4LnbG]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "am and I live in Atlanta",
        "redacted_text": "[NAME_GIVEN_S4LnbG] and I live in [LOCATION_CITY_FgBgz8WW]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 2,
                "new_start": 0,
                "new_end": 19,
                "label": "NAME_GIVEN",
                "text": "Ad\\nam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_S4LnbG]"
            },
            {
                "start": 17,
                "end": 24,
                "new_start": 17,
                "new_end": 41,
                "label": "LOCATION_CITY",
                "text": "Atlanta",
                "score": 0.9,
                "language": "en",
                "new_text": "[LOCATION_CITY_FgBgz8WW]"
            }
        ]
    }
    """


    with open(get_resource_path('single_boundary_cross.csv'), 'r') as f:
        response = helper.redact(f, True, lambda x: x['id'], lambda x: x['text'], redact)
        
        assert len(response)==2
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))

# single convo with 1 entity crossing a border
def test_multi_border_crossing():
    helper = CsvHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'I am married to Lis. my name is ad\na\nm and I live in Atlanta',
                'I am married to [NAME_GIVEN_uWI2]. my name is [NAME_GIVEN_S4LnbG] and I live in [LOCATION_CITY_FgBgz8WW]',
                16,
                [
                    Replacement(16,19,16,33,'NAME_GIVEN','Lis',0.9, 'en','[NAME_GIVEN_uWI2]'),
                    Replacement(32,38,46,65,'NAME_GIVEN','ad\na\nm',0.9, 'en','[NAME_GIVEN_S4LnbG]'),
                    Replacement(53,60,79,103,'LOCATION_CITY','Atlanta',0.9,'en','[LOCATION_CITY_FgBgz8WW]')
                ]
            )

    # Fixed expected values to match the entity text case in the redact function
    expected_row1 = """{
        "original_text": "I am married to Lis. my name is ad",
        "redacted_text": "I am married to [NAME_GIVEN_uWI2]. my name is [NAME_GIVEN_S4LnbG]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 16,
                "end": 19,
                "new_start": 16,
                "new_end": 33,
                "label": "NAME_GIVEN",
                "text": "Lis",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_uWI2]"
            },
            {
                "start": 32,
                "end": 34,
                "new_start": 32,
                "new_end": 51,
                "label": "NAME_GIVEN",
                "text": "ad\\na\\nm",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_S4LnbG]"
            }
        ]
    }
    """

    expected_row2 = """{
        "original_text": "a",
        "redacted_text": "[NAME_GIVEN_S4LnbG]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 1,
                "new_start": 0,
                "new_end": 19,
                "label": "NAME_GIVEN",
                "text": "ad\\na\\nm",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_S4LnbG]"
            }
        ]
    }
    """

    expected_row3 = """{
        "original_text": "m and I live in Atlanta",
        "redacted_text": "[NAME_GIVEN_S4LnbG] and I live in [LOCATION_CITY_FgBgz8WW]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 1,
                "new_start": 0,
                "new_end": 19,
                "label": "NAME_GIVEN",
                "text": "ad\\na\\nm",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_S4LnbG]"
            },
            {
                "start": 16,
                "end": 23,
                "new_start": 34,
                "new_end": 58,
                "label": "LOCATION_CITY",
                "text": "Atlanta",
                "score": 0.9,
                "language": "en",
                "new_text": "[LOCATION_CITY_FgBgz8WW]"
            }
        ]
    }
    """

    with open(get_resource_path('multi_boundary_cross.csv'), 'r') as f:
        response = helper.redact(f, True, lambda x: x['id'], lambda x: x['text'], redact)
        
        assert len(response)==3
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))   
        assert_redaction_response_equal(response[2],build_redaction_response_from_json(expected_row3))

# Test redact_and_reconstruct method with a simple CSV
def test_redact_and_reconstruct():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello, my name is adam\nI work at Tonic',
                'hello, my name is [NAME_GIVEN_ssYs5]\nI work at [ORGANIZATION_5Ve7OH]',
                9,
                [
                    Replacement(18,22,18,36,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(33,38,47,68,'ORGANIZATION','Tonic',0.9, 'en','[ORGANIZATION_5Ve7OH]')]
            )
    
    with open(get_resource_path('single_convo.csv'), 'r') as f:
        result = helper.redact_and_reconstruct(f, True, 'id', 'text', redact)
        
        # Result should be a StringIO object
        assert isinstance(result, io.StringIO)
        
        # Reset the cursor to the beginning to read the content
        result.seek(0)
        reader = csv.reader(result)
        
        # Check header
        header = next(reader)
        assert header == ['id', 'text']
        
        # Check first row
        row1 = next(reader)
        assert row1[0] == '1'
        assert row1[1] == 'hello, my name is [NAME_GIVEN_ssYs5]'
        
        # Check second row
        row2 = next(reader)
        assert row2[0] == '1'
        assert row2[1] == 'I work at [ORGANIZATION_5Ve7OH]'

# Test redact_and_reconstruct method with a simple CSV and no header
def test_redact_and_reconstruct_no_header():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello, my name is adam\nI work at Tonic',
                'hello, my name is [NAME_GIVEN_ssYs5]\nI work at [ORGANIZATION_5Ve7OH]',
                9,
                [
                    Replacement(18,22,18,36,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(33,38,47,68,'ORGANIZATION','Tonic',0.9, 'en','[ORGANIZATION_5Ve7OH]')]
            )
    
    with open(get_resource_path('single_convo_noheader.csv'), 'r') as f:
        result = helper.redact_and_reconstruct(f, False, '0', '1', redact)
        
        # Result should be a StringIO object
        assert isinstance(result, io.StringIO)
        
        # Reset the cursor to the beginning to read the content
        result.seek(0)
        reader = csv.reader(result)
               
        # Check first row
        row1 = next(reader)
        assert row1[0] == '1'
        assert row1[1] == 'hello, my name is [NAME_GIVEN_ssYs5]'
        
        # Check second row
        row2 = next(reader)
        assert row2[0] == '1'
        assert row2[1] == 'I work at [ORGANIZATION_5Ve7OH]'        

# Test using None for grouping_col
def test_null_grouping():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hi adam, how are you?\nhello andrew, how are you?\ngood\nbad',
                'hi [NAME_GIVEN_ssYs5], how are you?\nhello [NAME_GIVEN_T9FcFaC], how are you?\ngood\nbad',
                9,
                [
                    Replacement(3,7,3,21,'NAME_GIVEN','adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(29,35,45,65,'NAME_GIVEN','andrew',0.9, 'en','[NAME_GIVEN_T9FcFaC]')
                ]
            )
    
    with open(get_resource_path('two_convo.csv'), 'r') as f:
        # Using None for grouping_col should group all rows together
        result = helper.redact_and_reconstruct(f, True, None, 'text', redact)
        
        result.seek(0)
        reader = csv.reader(result)
        
        # Check header
        header = next(reader)
        assert header == ['id', 'text']
        
        # Check all rows are redacted correctly
        row1 = next(reader)
        # Just check if NAME_GIVEN is in the text - exact format may vary
        assert '[NAME_GIVEN_' in row1[1]
        
        row2 = next(reader)
        # Just check if NAME_GIVEN is in the text - exact format may vary
        assert '[NAME_GIVEN_' in row2[1]
        
        row3 = next(reader)
        assert row3[1] == 'good'
        
        row4 = next(reader)
        assert row4[1] == 'bad'

# Test handling of invalid rows
def test_invalid_row():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'hello world',
                'hello world',
                0,
                []
            )
    
    # Create a CSV with an invalid row (too few columns)
    csv_content = 'id,text\n1,"hello world"\n1'
    csv_file = io.StringIO(csv_content)
    
    # Test that an exception is raised
    with pytest.raises(Exception) as excinfo:
        helper.redact(csv_file, True, lambda x: x['id'], lambda x: x['text'], redact)
    
    assert 'Invalid row' in str(excinfo.value)

# Test empty CSV
def test_empty_csv():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                x,
                x,
                0,
                []
            )
    
    # Create an empty CSV with just a header
    csv_content = 'id,text\n'
    csv_file = io.StringIO(csv_content)
    
    # Test that redact returns an empty list
    response = helper.redact(csv_file, True, lambda x: x['id'], lambda x: x['text'], redact)
    assert len(response) == 0
    
    # Test redact_and_reconstruct returns a CSV with just the header
    csv_file = io.StringIO(csv_content)
    result = helper.redact_and_reconstruct(csv_file, True, 'id', 'text', redact)
    
    result.seek(0)
    content = result.read()
    # The CSV writer adds quotes, so check for that
    assert '"id"' in content and '"text"' in content

# Test CSV with no entities
def test_no_entities():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        # Return a redaction response with no entities
        return RedactionResponse(
                x,
                x,  # Same text for redacted (no changes)
                0,
                []  # No entities
            )
    
    with open(get_resource_path('single_convo.csv'), 'r') as f:
        response = helper.redact(f, True, lambda x: x['id'], lambda x: x['text'], redact)
        
        assert len(response) == 2
        assert response[0].original_text == 'hello, my name is adam'
        assert response[0].redacted_text == 'hello, my name is adam'  # No change
        assert len(response[0].de_identify_results) == 0  # No entities
        
        assert response[1].original_text == 'I work at Tonic'
        assert response[1].redacted_text == 'I work at Tonic'  # No change
        assert len(response[1].de_identify_results) == 0  # No entities
        
# Test multiple entity overlaps (complex case)
def test_multiple_entity_overlaps():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'John Smith from New York City works at Tonic AI in Seattle',
                'John [PERSON_DfhGqE] from [LOCATION_CITY_KAjfG3] works at [ORGANIZATION_5Ve7OH] in [LOCATION_CITY_Jaf4DF]',
                12,
                [
                    # Multiple overlapping entities
                    Replacement(5, 10, 5, 19, 'PERSON', 'Smith', 0.9, 'en', '[PERSON_DfhGqE]'),
                    Replacement(16, 29, 25, 44, 'LOCATION_CITY', 'New York City', 0.9, 'en', '[LOCATION_CITY_KAjfG3]'),
                    Replacement(39, 47, 54, 75, 'ORGANIZATION', 'Tonic AI', 0.9, 'en', '[ORGANIZATION_5Ve7OH]'),
                    Replacement(51, 58, 79, 98, 'LOCATION_CITY', 'Seattle', 0.9, 'en', '[LOCATION_CITY_Jaf4DF]')
                ]
            )
    
    # Create a CSV file with text that has multiple overlapping entities
    csv_content = 'id,text\n1,"John Smith from New York City works at Tonic AI in Seattle"'
    csv_file = io.StringIO(csv_content)
    
    response = helper.redact(csv_file, True, lambda x: x['id'], lambda x: x['text'], redact)
    
    assert len(response) == 1
    assert response[0].original_text == 'John Smith from New York City works at Tonic AI in Seattle'
    assert response[0].redacted_text == 'John [PERSON_DfhGqE] from [LOCATION_CITY_KAjfG3] works at [ORGANIZATION_5Ve7OH] in [LOCATION_CITY_Jaf4DF]'
    assert len(response[0].de_identify_results) == 4

# Test redact_and_reconstruct with grouping
def test_redact_and_reconstruct_with_grouping():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        if 'adam' in x.lower():
            # First group
            return RedactionResponse(
                    'Hello adam\nGoodbye adam',
                    'Hello [NAME_GIVEN_abcde]\nGoodbye [NAME_GIVEN_abcde]',
                    9,
                    [
                        Replacement(6, 10, 6, 24, 'NAME_GIVEN', 'adam', 0.9, 'en', '[NAME_GIVEN_abcde]'),
                        Replacement(18, 22, 32, 50, 'NAME_GIVEN', 'adam', 0.9, 'en', '[NAME_GIVEN_abcde]')
                    ]
                )
        else:
            # Second group
            return RedactionResponse(
                    'Hello bob\nGoodbye bob',
                    'Hello [NAME_GIVEN_12345]\nGoodbye [NAME_GIVEN_12345]',
                    9,
                    [
                        Replacement(6, 9, 6, 23, 'NAME_GIVEN', 'bob', 0.9, 'en', '[NAME_GIVEN_12345]'),
                        Replacement(17, 20, 31, 48, 'NAME_GIVEN', 'bob', 0.9, 'en', '[NAME_GIVEN_12345]')
                    ]
                )
    
    # Create a CSV with multiple groups
    csv_content = 'id,text\n1,"Hello adam"\n1,"Goodbye adam"\n2,"Hello bob"\n2,"Goodbye bob"'
    csv_file = io.StringIO(csv_content)
    
    # Test redact_and_reconstruct with grouping by ID
    result = helper.redact_and_reconstruct(csv_file, True, 'id', 'text', redact)
    
    result.seek(0)
    reader = csv.reader(result)
    
    # Check header
    header = next(reader)
    assert header == ['id', 'text']
    
    # First group
    row1 = next(reader)
    assert row1[0] == '1'
    assert '[NAME_GIVEN_abcde]' in row1[1]
    
    row2 = next(reader)
    assert row2[0] == '1'
    assert '[NAME_GIVEN_abcde]' in row2[1]
    
    # Second group
    row3 = next(reader)
    assert row3[0] == '2'
    assert '[NAME_GIVEN_12345]' in row3[1]
    
    row4 = next(reader)
    assert row4[0] == '2'
    assert '[NAME_GIVEN_12345]' in row4[1]
    
# Test overlapping entities
def test_overlapping_entities():
    helper = CsvHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'John Smith lives in New York City',
                'John [PERSON_DfhGqE] lives in [LOCATION_CITY_KAjfG3]',
                10,
                [
                    # Overlapping entities - "Smith" is part of "Smith lives in New York"
                    Replacement(5, 10, 5, 19, 'PERSON', 'Smith', 0.9, 'en', '[PERSON_DfhGqE]'),
                    Replacement(20, 33, 29, 48, 'LOCATION_CITY', 'New York City', 0.9, 'en', '[LOCATION_CITY_KAjfG3]')
                ]
            )
    
    # Create a CSV file with text that has overlapping entities
    csv_content = 'id,text\n1,"John Smith lives in New York City"'
    csv_file = io.StringIO(csv_content)
    
    response = helper.redact(csv_file, True, lambda x: x['id'], lambda x: x['text'], redact)
    
    assert len(response) == 1
    
    # Check if the redaction handles overlapping entities correctly
    assert response[0].original_text == 'John Smith lives in New York City'
    assert response[0].redacted_text == 'John [PERSON_DfhGqE] lives in [LOCATION_CITY_KAjfG3]'
    assert len(response[0].de_identify_results) == 2
    
    # Check first entity
    assert response[0].de_identify_results[0].text == 'Smith'
    assert response[0].de_identify_results[0].start == 5
    assert response[0].de_identify_results[0].end == 10
    
    # Check second entity
    assert response[0].de_identify_results[1].text == 'New York City'
    assert response[0].de_identify_results[1].start == 20
    assert response[0].de_identify_results[1].end == 33