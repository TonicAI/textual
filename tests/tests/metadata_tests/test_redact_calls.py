from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.redact_api import TextualNer
from datetime import datetime

def test_names(textual: TextualNer):
    response = textual.redact("My name is Adam. Again, my name is adam.", generator_default='Synthesis')
    assert response.de_identify_results[0].new_text.lower() == response.de_identify_results[1].new_text.lower(), "By default, name generator is case insensitive"
    
    response = textual.redact("My name is Adam. Again, my name is adam.", generator_default='Synthesis', generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(is_consistency_case_sensitive=True)})
    assert response.de_identify_results[0].new_text.lower() != response.de_identify_results[1].new_text.lower(), "We should adhere to metadata and names should be different with different casings"

    #response1 = textual.redact("My name is Adam.", generator_default='Synthesis', generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=True)})
    #response2 = textual.redact("My name is Adam.", generator_default='Synthesis', generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=False)})
    #assert response1.de_identify_results[0].new_text != response2.de_identify_results[0].new_text, "Preserving gender affects results"

def test_hipaa_address(textual: TextualNer):
    response = textual.redact("I live in Atlanta, GA.", generator_default='Synthesis', generator_config={'LOCATION_CITY':'Off'})
    assert response.de_identify_results[0].new_text == 'GA', "HIPAA Address generator doesn't synthesize states"

    response = textual.redact("I live in Atlanta, GA.", generator_default='Synthesis', generator_config={'LOCATION_CITY':'Off'}, generator_metadata={'LOCATION_STATE': HipaaAddressGeneratorMetadata(use_non_hipaa_address_generator=True)})
    assert response.de_identify_results[0].new_text != 'GA', "non-HIPAA Address generator does synthesize states"
        
    response = textual.redact("I live in Atlanta, GA. 30305.", generator_default='Off', generator_config={'LOCATION_ZIP':'Synthesis'})
    assert response.de_identify_results[0].new_text.startswith('303') and not response.de_identify_results[0].new_text.endswith('00'), "by default, we replace last 2 of zip "
        
    response = textual.redact("I live in Atlanta, GA. 30305.", generator_default='Off', generator_config={'LOCATION_ZIP':'Synthesis'}, generator_metadata={'LOCATION_ZIP': HipaaAddressGeneratorMetadata(replace_truncated_zeros_in_zip_code=False)})
    assert response.de_identify_results[0].new_text.startswith('303') and response.de_identify_results[0].new_text.endswith('00'), "we replace last 2 of zip with zeros "
    
    response = textual.redact("I live in AtLaNtA", generator_default='Synthesis', generator_metadata={'LOCATION_CITY': HipaaAddressGeneratorMetadata(realistic_synthetic_values=False)})
    new_val = response.de_identify_results[0].new_text
    assert new_val[0].isupper()
    assert new_val[1].islower()
    assert new_val[2].isupper()
    assert new_val[3].islower()
    assert new_val[4].isupper()
    assert new_val[5].islower()
    assert new_val[6].isupper()

def test_numeric_value(textual: TextualNer):
    response = textual.redact("My ID is 123", generator_default='Off', generator_config={'NUMERIC_VALUE': 'Synthesis'})
    assert len(response.de_identify_results[0].new_text) == 3 and response.de_identify_results[0].new_text != '123'

    response = textual.redact("My ID is 123", generator_default='Off', generator_config={'NUMERIC_VALUE': 'Synthesis'}, generator_metadata={'NUMERIC_VALUE':NumericValueGeneratorMetadata(use_oracle_integer_pk_generator=True)})
    assert len(response.de_identify_results[0].new_text) > 10

def test_phone_number(textual: TextualNer):
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default='Off',
        generator_config={'PHONE_NUMBER': 'Synthesis'},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=True)})
    assert is_all_digits(response.de_identify_results[0].new_text)

    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default='Off',
        generator_config={'PHONE_NUMBER': 'Synthesis'},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=False)})
    assert not is_all_digits(response.de_identify_results[0].new_text)

    
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default='Off',
        generator_config={'PHONE_NUMBER': 'Synthesis'},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=True)})
    assert not is_all_digits(response.de_identify_results[0].new_text)
        
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default='Off',
        generator_config={'PHONE_NUMBER': 'Synthesis'},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=False)})
    assert not is_all_digits(response.de_identify_results[0].new_text)

def test_date_time(textual: TextualNer):
    response = textual.redact(
        "I have an appointment on 08xx07xx2024.",
        generator_default='Off',
        generator_config={'DATE_TIME':'Synthesis'},
        label_allow_lists={'DATE_TIME':['08xx07xx2024']},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(additional_date_formats=['dd\'xx\'MM\'xx\'yyyy'])})
    assert response.de_identify_results[0].new_text == '06xx07xx2024'

    response = textual.redact("I have an appointment on 08-13-2024. That is 3 days before 08-16-24.  It is 7 days before 08-20-2024 and a month before 09-13-2024.",
        generator_default='Off',
        generator_config={'DATE_TIME':'Synthesis'},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(apply_constant_shift_to_document=True)})

    response = textual.redact("I have an appointment on 08-13-2024",
        generator_default='Off',
        generator_config={'DATE_TIME':'Synthesis'},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(timestamp_shift_metadata=TimestampShiftMetadata(timestamp_shift_in_days=10000))})
    assert response.de_identify_results[0].new_text == '09-11-2030'

def test_age(textual: TextualNer):
    response = textual.redact("I am 38 years old", generator_default='Off',generator_config={'PERSON_AGE':'Synthesis'})
    assert response.de_identify_results[0].new_text == '44'

    response = textual.redact("I am 38 years old",
        generator_default='Off',
        generator_config={'PERSON_AGE':'Synthesis'},
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(age_shift_metadata=AgeShiftMetadata(age_shift_in_years=500))})
    assert response.de_identify_results[0].new_text == '536'

    response = textual.redact("I am 97 years old",
        generator_default='Off',
        generator_config={'PERSON_AGE':'Synthesis'},
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(age_shit_metadata=AgeShiftMetadata(age_shift_in_years=5))})
    assert response.de_identify_results[0].new_text == '92'

def is_all_digits(val: str):
    for c in val:
        if not c.isdigit():
            return False
    return True