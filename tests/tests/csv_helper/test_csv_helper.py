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