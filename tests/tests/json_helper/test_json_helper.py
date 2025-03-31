import json

from tests.utils.assertion_utils import assert_redaction_response_equal
from tests.utils.redaction_response_utils import build_redaction_response_from_json
from tests.utils.resource_utils import get_resource_path
from tonic_textual.classes.common_api_responses.replacement import Replacement
from tonic_textual.classes.redact_api_responses.redaction_response import RedactionResponse
from tonic_textual.helpers.json_conversation_helper import JsonConversationHelper

def test_simple_json_conversation():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'Hi, this is Adam\nHi Adam, nice to meet you this is Jane.',
                'Hi, this is [NAME_GIVEN_ssYs5]\nHi [NAME_GIVEN_ssYs5], nice to meet you this is [NAME_GIVEN_7u9Zx].',
                9,
                [
                    Replacement(12,16,12,30,'NAME_GIVEN','Adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(20,24,34,52,'NAME_GIVEN','Adam',0.9, 'en','[NAME_GIVEN_ssYs5]'),
                    Replacement(55,59,83,101,'NAME_GIVEN','Jane',0.9, 'en','[NAME_GIVEN_7u9Zx]')
                ]
            )

    expected_part1 = """{
        "original_text": "Hi, this is Adam",
        "redacted_text": "Hi, this is [NAME_GIVEN_ssYs5]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 12,
                "end": 16,
                "new_start": 12,
                "new_end": 30,
                "label": "NAME_GIVEN",
                "text": "Adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    expected_part2 = """{
        "original_text": "Hi Adam, nice to meet you this is Jane.",
        "redacted_text": "Hi [NAME_GIVEN_ssYs5], nice to meet you this is [NAME_GIVEN_7u9Zx].",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 3,
                "end": 7,
                "new_start": 3,
                "new_end": 21,
                "label": "NAME_GIVEN",
                "text": "Adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            },
            {
                "start": 38,
                "end": 42,
                "new_start": 52,
                "new_end": 70,
                "label": "NAME_GIVEN",
                "text": "Jane",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_7u9Zx]"
            }
        ]
    }
    """

    with open(get_resource_path('simple_conversation.json'), 'r') as f:
        conversation = json.load(f)
        response = helper.redact(
            conversation, 
            lambda x: x["conversation"]["transcript"], 
            lambda x: x["content"], 
            redact
        )
        
        assert len(response) == 2
        assert_redaction_response_equal(response[0], build_redaction_response_from_json(expected_part1))
        assert_redaction_response_equal(response[1], build_redaction_response_from_json(expected_part2))

def test_boundary_crossing_entity():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'Hello, my name is An\ndrew Smith and I\'m from Seattle\nNice to meet you An\ndrew. I\'m Jane Johnson from New York City',
                'Hello, my name is [NAME_GIVEN_1Ab3d]\n[NAME_GIVEN_1Ab3d] and I\'m from [LOCATION_CITY_8jH2k]\nNice to meet you [NAME_GIVEN_1Ab3d]\n[NAME_GIVEN_1Ab3d]. I\'m [NAME_GIVEN_7u9Zx] [NAME_GIVEN_4Tf6g] from [LOCATION_CITY_9pL3m]',
                15,
                [
                    # Entity that spans boundaries between parts 1 and 2
                    Replacement(17,23,17,35,'NAME_GIVEN','An\ndrew',0.9, 'en','[NAME_GIVEN_1Ab3d]'),
                    # Entity in part 2
                    Replacement(39,46,51,69,'LOCATION_CITY','Seattle',0.9, 'en','[LOCATION_CITY_8jH2k]'),
                    # Entity that spans boundaries between parts 3 and 4
                    Replacement(64,70,83,101,'NAME_GIVEN','An\ndrew',0.9, 'en','[NAME_GIVEN_1Ab3d]'),
                    # Entities in part 4
                    Replacement(79,83,110,128,'NAME_GIVEN','Jane',0.9, 'en','[NAME_GIVEN_7u9Zx]'),
                    Replacement(84,91,129,147,'NAME_GIVEN','Johnson',0.9, 'en','[NAME_GIVEN_4Tf6g]'),
                    Replacement(97,109,153,171,'LOCATION_CITY','New York City',0.9, 'en','[LOCATION_CITY_9pL3m]')
                ]
            )

    expected_part1 = """{
        "original_text": "Hello, my name is An",
        "redacted_text": "Hello, my name is [NAME_GIVEN_1Ab3d]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 17,
                "end": 19,
                "new_start": 17,
                "new_end": 35,
                "label": "NAME_GIVEN",
                "text": "An\\ndrew",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_1Ab3d]"
            }
        ]
    }
    """

    expected_part2 = """{
        "original_text": "drew Smith and I'm from Seattle",
        "redacted_text": "[NAME_GIVEN_1Ab3d] and I'm from [LOCATION_CITY_8jH2k]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 4,
                "new_start": 0,
                "new_end": 18,
                "label": "NAME_GIVEN",
                "text": "An\\ndrew",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_1Ab3d]"
            },
            {
                "start": 24,
                "end": 31,
                "new_start": 36,
                "new_end": 54,
                "label": "LOCATION_CITY",
                "text": "Seattle",
                "score": 0.9,
                "language": "en",
                "new_text": "[LOCATION_CITY_8jH2k]"
            }
        ]
    }
    """

    expected_part3 = """{
        "original_text": "Nice to meet you An",
        "redacted_text": "Nice to meet you [NAME_GIVEN_1Ab3d]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 16,
                "end": 18,
                "new_start": 16,
                "new_end": 34,
                "label": "NAME_GIVEN",
                "text": "An\\ndrew",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_1Ab3d]"
            }
        ]
    }
    """

    expected_part4 = """{
        "original_text": "drew. I'm Jane Johnson from New York City",
        "redacted_text": "[NAME_GIVEN_1Ab3d]. I'm [NAME_GIVEN_7u9Zx] [NAME_GIVEN_4Tf6g] from [LOCATION_CITY_9pL3m]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 4,
                "new_start": 0,
                "new_end": 18,
                "label": "NAME_GIVEN",
                "text": "An\\ndrew",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_1Ab3d]"
            },
            {
                "start": 9,
                "end": 13,
                "new_start": 24,
                "new_end": 42,
                "label": "NAME_GIVEN",
                "text": "Jane",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_7u9Zx]"
            },
            {
                "start": 14,
                "end": 21,
                "new_start": 43,
                "new_end": 61,
                "label": "NAME_GIVEN",
                "text": "Johnson",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_4Tf6g]"
            },
            {
                "start": 27,
                "end": 39,
                "new_start": 67,
                "new_end": 85,
                "label": "LOCATION_CITY",
                "text": "New York City",
                "score": 0.9,
                "language": "en",
                "new_text": "[LOCATION_CITY_9pL3m]"
            }
        ]
    }
    """

    with open(get_resource_path('complex_conversation.json'), 'r') as f:
        conversation = json.load(f)
        response = helper.redact(
            conversation, 
            lambda x: x["conversation"]["transcript"], 
            lambda x: x["content"], 
            redact
        )
        
        assert len(response) == 4
        assert_redaction_response_equal(response[0], build_redaction_response_from_json(expected_part1))
        assert_redaction_response_equal(response[1], build_redaction_response_from_json(expected_part2))
        assert_redaction_response_equal(response[2], build_redaction_response_from_json(expected_part3))
        assert_redaction_response_equal(response[3], build_redaction_response_from_json(expected_part4))

def test_empty_json_conversation():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                '',
                '',
                0,
                []
            )

    # Create an empty conversation with no text parts
    empty_conversation = {
        "conversation": {
            "transcript": []
        }
    }
    
    response = helper.redact(
        empty_conversation, 
        lambda x: x["conversation"]["transcript"], 
        lambda x: x["content"], 
        redact
    )
    
    assert len(response) == 0

def test_single_entity_json_conversation():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'Hi, this is Adam',
                'Hi, this is [NAME_GIVEN_ssYs5]',
                5,
                [
                    Replacement(12,16,12,30,'NAME_GIVEN','Adam',0.9, 'en','[NAME_GIVEN_ssYs5]')
                ]
            )

    expected_part = """{
        "original_text": "Hi, this is Adam",
        "redacted_text": "Hi, this is [NAME_GIVEN_ssYs5]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 12,
                "end": 16,
                "new_start": 12,
                "new_end": 30,
                "label": "NAME_GIVEN",
                "text": "Adam",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_ssYs5]"
            }
        ]
    }
    """

    # Create a simple conversation with a single text part
    single_conversation = {
        "conversation": {
            "transcript": [
                {"speaker": "speaker1", "content": "Hi, this is Adam"}
            ]
        }
    }
    
    response = helper.redact(
        single_conversation, 
        lambda x: x["conversation"]["transcript"], 
        lambda x: x["content"], 
        redact
    )
    
    assert len(response) == 1
    assert_redaction_response_equal(response[0], build_redaction_response_from_json(expected_part))

def test_no_entities_json_conversation():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        # Return a redaction response with no entities
        return RedactionResponse(
                x,
                x,  # Same text for redacted (no changes)
                0,
                []  # No entities
            )
    
    # Create a simple conversation with no entities
    conversation = {
        "conversation": {
            "transcript": [
                {"speaker": "speaker1", "content": "Hello there"},
                {"speaker": "speaker2", "content": "How are you doing today?"}
            ]
        }
    }
    
    response = helper.redact(
        conversation, 
        lambda x: x["conversation"]["transcript"], 
        lambda x: x["content"], 
        redact
    )
    
    assert len(response) == 2
    assert response[0].original_text == "Hello there"
    assert response[0].redacted_text == "Hello there"  # No change
    assert len(response[0].de_identify_results) == 0  # No entities
    
    assert response[1].original_text == "How are you doing today?"
    assert response[1].redacted_text == "How are you doing today?"  # No change
    assert len(response[1].de_identify_results) == 0  # No entities

def test_multiple_entity():
    helper = JsonConversationHelper()
    
    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'John Smith from New York City works at Tonic AI',
                'John [PERSON_DfhGqE] from [LOCATION_CITY_KAjfG3] works at [ORGANIZATION_5Ve7OH]',
                12,
                [
                    # Multiple entities
                    Replacement(5, 10, 5, 19, 'PERSON', 'Smith', 0.9, 'en', '[PERSON_DfhGqE]'),
                    Replacement(16, 29, 25, 44, 'LOCATION_CITY', 'New York City', 0.9, 'en', '[LOCATION_CITY_KAjfG3]'),
                    Replacement(39, 47, 54, 75, 'ORGANIZATION', 'Tonic AI', 0.9, 'en', '[ORGANIZATION_5Ve7OH]')
                ]
            )
    
    # Create a conversation with multiple entities
    conversation = {
        "conversation": {
            "transcript": [
                {"speaker": "speaker1", "content": "John Smith from New York City works at Tonic AI"}
            ]
        }
    }
    
    response = helper.redact(
        conversation, 
        lambda x: x["conversation"]["transcript"], 
        lambda x: x["content"], 
        redact
    )
    
    expected_part = """{
        "original_text": "John Smith from New York City works at Tonic AI",
        "redacted_text": "John [PERSON_DfhGqE] from [LOCATION_CITY_KAjfG3] works at [ORGANIZATION_5Ve7OH]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 5,
                "end": 10,
                "new_start": 5,
                "new_end": 19,
                "label": "PERSON",
                "text": "Smith",
                "score": 0.9,
                "language": "en",
                "new_text": "[PERSON_DfhGqE]"
            },
            {
                "start": 16,
                "end": 29,
                "new_start": 25,
                "new_end": 44,
                "label": "LOCATION_CITY",
                "text": "New York City",
                "score": 0.9,
                "language": "en",
                "new_text": "[LOCATION_CITY_KAjfG3]"
            },
            {
                "start": 39,
                "end": 47,
                "new_start": 54,
                "new_end": 75,
                "label": "ORGANIZATION",
                "text": "Tonic AI",
                "score": 0.9,
                "language": "en",
                "new_text": "[ORGANIZATION_5Ve7OH]"
            }
        ]
    }
    """
    
    assert len(response) == 1
    assert_redaction_response_equal(response[0], build_redaction_response_from_json(expected_part))

# single convo with 1 entity crossing a border
def test_multi_border_crossing():
    helper = JsonConversationHelper()

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

    with open(get_resource_path('multi_boundary_cross.json'), 'r') as f:
        conversation = json.load(f)
        response = helper.redact(
            conversation, 
            lambda x: x["conversation"]["transcript"], 
            lambda x: x["content"], 
            redact
        )
        
        assert len(response)==3
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_row1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_row2))   
        assert_redaction_response_equal(response[2],build_redaction_response_from_json(expected_row3))

def test_complex_multi_part_crossing():
    helper = JsonConversationHelper()

    def redact(x) -> RedactionResponse:
        return RedactionResponse(
                'My full name is Alex\nan\nder\nJones and I work at Google\nNice to meet you Alexander',
                'My full name is [NAME_GIVEN_Xz7a8]\n[NAME_GIVEN_Xz7a8]\n[NAME_GIVEN_Xz7a8]\n[NAME_GIVEN_Xz7a8] and I work at [ORGANIZATION_5Ve7OH]\nNice to meet you [NAME_GIVEN_B4s2p]',
                20,
                [
                    # Entity that spans 4 parts
                    Replacement(15,29,15,33,'NAME_GIVEN','Alex\nan\nder\nJones',0.9, 'en','[NAME_GIVEN_Xz7a8]'),
                    # Entity that is only in 4th part
                    Replacement(42,48,46,67,'ORGANIZATION','Google',0.9, 'en','[ORGANIZATION_5Ve7OH]'),
                    # Entity in 5th part only
                    Replacement(66,75,85,103,'NAME_GIVEN','Alexander',0.9, 'en','[NAME_GIVEN_B4s2p]')
                ]
            )

    expected_part1 = """{
        "original_text": "My full name is Alex",
        "redacted_text": "My full name is [NAME_GIVEN_Xz7a8]",
        "usage": -1,
        "de_identify_results": [
            {
                "start": 15,
                "end": 19,
                "new_start": 15,
                "new_end": 33,
                "label": "NAME_GIVEN",
                "text": "Alex\\nan\\nder\\nJones",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_Xz7a8]"
            }
        ]
    }
    """

    expected_part2 = """{
        "original_text": "an",
        "redacted_text": "[NAME_GIVEN_Xz7a8]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 2,
                "new_start": 0,
                "new_end": 18,
                "label": "NAME_GIVEN",
                "text": "Alex\\nan\\nder\\nJones",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_Xz7a8]"
            }
        ]
    }
    """

    expected_part3 = """{
        "original_text": "der",
        "redacted_text": "[NAME_GIVEN_Xz7a8]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 3,
                "new_start": 0,
                "new_end": 18,
                "label": "NAME_GIVEN",
                "text": "Alex\\nan\\nder\\nJones",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_Xz7a8]"
            }
        ]
    }
    """

    expected_part4 = """{
        "original_text": "Jones and I work at Google",
        "redacted_text": "[NAME_GIVEN_Xz7a8] and I work at [ORGANIZATION_5Ve7OH]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 0,
                "end": 5,
                "new_start": 0,
                "new_end": 18,
                "label": "NAME_GIVEN",
                "text": "Alex\\nan\\nder\\nJones",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_Xz7a8]"
            },
            {
                "start": 18,
                "end": 24,
                "new_start": 31,
                "new_end": 52,
                "label": "ORGANIZATION",
                "text": "Google",
                "score": 0.9,
                "language": "en",
                "new_text": "[ORGANIZATION_5Ve7OH]"
            }
        ]
    }
    """

    expected_part5 = """{
        "original_text": "Nice to meet you Alexander",
        "redacted_text": "Nice to meet you [NAME_GIVEN_B4s2p]",      
        "usage": -1,
        "de_identify_results": [
            {
                "start": 16,
                "end": 25,
                "new_start": 16,
                "new_end": 34,
                "label": "NAME_GIVEN",
                "text": "Alexander",
                "score": 0.9,
                "language": "en",
                "new_text": "[NAME_GIVEN_B4s2p]"
            }
        ]
    }
    """

    with open(get_resource_path('multi_part_complex.json'), 'r') as f:
        conversation = json.load(f)
        response = helper.redact(
            conversation, 
            lambda x: x["conversation"]["transcript"], 
            lambda x: x["content"], 
            redact
        )
        
        assert len(response)==5
        assert_redaction_response_equal(response[0],build_redaction_response_from_json(expected_part1))
        assert_redaction_response_equal(response[1],build_redaction_response_from_json(expected_part2))
        assert_redaction_response_equal(response[2],build_redaction_response_from_json(expected_part3))
        assert_redaction_response_equal(response[3],build_redaction_response_from_json(expected_part4))
        assert_redaction_response_equal(response[4],build_redaction_response_from_json(expected_part5))    