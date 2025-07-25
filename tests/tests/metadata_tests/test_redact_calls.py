from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.redact_api import TextualNer
from datetime import datetime

import re

def test_names(textual: TextualNer):
    response = textual.redact("My name is Adam. Again, my name is adam.", generator_default=PiiState.Synthesis)
    assert response.de_identify_results[0].new_text.lower() == response.de_identify_results[1].new_text.lower(), "By default, name generator is case insensitive"
    
    response = textual.redact("My name is Adam. Again, my name is adam.", generator_default=PiiState.Synthesis, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(is_consistency_case_sensitive=True)})
    assert response.de_identify_results[0].new_text.lower() != response.de_identify_results[1].new_text.lower(), "We should adhere to metadata and names should be different with different casings"

    response1 = textual.redact("My name is Adam.", generator_default=PiiState.Synthesis, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=True)})
    response2 = textual.redact("My name is Adam.", generator_default=PiiState.Synthesis, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=False)})
    assert response1.de_identify_results[0].new_text != response2.de_identify_results[0].new_text, "Preserving gender affects results"

def test_hipaa_address(textual: TextualNer):
    response = textual.redact("I live in Atlanta, GA.", generator_default=PiiState.Synthesis, generator_config={'LOCATION_CITY':PiiState.Off})
    assert response.de_identify_results[0].new_text == 'GA', "HIPAA Address generator doesn't synthesize states"

    response = textual.redact("I live in Atlanta, GA.", generator_default=PiiState.Synthesis, generator_config={'LOCATION_CITY':PiiState.Off}, generator_metadata={'LOCATION_STATE': HipaaAddressGeneratorMetadata(use_non_hipaa_address_generator=True)})
    assert response.de_identify_results[0].new_text != 'GA', "non-HIPAA Address generator does synthesize states"
        
    response = textual.redact("I live in Atlanta, GA. 30305.", generator_default=PiiState.Off, generator_config={'LOCATION_ZIP':PiiState.Synthesis})
    assert response.de_identify_results[0].new_text.startswith('303') and not response.de_identify_results[0].new_text.endswith('00'), "by default, we replace last 2 of zip "
        
    response = textual.redact("I live in Atlanta, GA. 30305.", generator_default=PiiState.Off, generator_config={'LOCATION_ZIP':PiiState.Synthesis}, generator_metadata={'LOCATION_ZIP': HipaaAddressGeneratorMetadata(replace_truncated_zeros_in_zip_code=False)})
    assert response.de_identify_results[0].new_text.startswith('303') and response.de_identify_results[0].new_text.endswith('00'), "we replace last 2 of zip with zeros "
    
    response = textual.redact("I live in AtLaNtA", generator_default=PiiState.Synthesis, generator_metadata={'LOCATION_CITY': HipaaAddressGeneratorMetadata(realistic_synthetic_values=False)})
    new_val = response.de_identify_results[0].new_text
    assert new_val[0].isupper()
    assert new_val[1].islower()
    assert new_val[2].isupper()
    assert new_val[3].islower()
    assert new_val[4].isupper()
    assert new_val[5].islower()
    assert new_val[6].isupper()

def test_numeric_value(textual: TextualNer):
    response = textual.redact("My ID is 123", generator_default=PiiState.Off, generator_config={'NUMERIC_VALUE': PiiState.Synthesis})
    assert len(response.de_identify_results[0].new_text) == 3 and response.de_identify_results[0].new_text != '123'

    response = textual.redact("My ID is 123", generator_default=PiiState.Off, generator_config={'NUMERIC_VALUE': PiiState.Synthesis}, generator_metadata={'NUMERIC_VALUE':NumericValueGeneratorMetadata(use_oracle_integer_pk_generator=True)})
    assert len(response.de_identify_results[0].new_text) > 10

def test_phone_number(textual: TextualNer):
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default=PiiState.Off,
        generator_config={'PHONE_NUMBER': PiiState.Synthesis},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=True)})
    assert is_all_digits(response.de_identify_results[0].new_text)

    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default=PiiState.Off,
        generator_config={'PHONE_NUMBER': PiiState.Synthesis},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=False)})
    assert not is_all_digits(response.de_identify_results[0].new_text)

    
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default=PiiState.Off,
        generator_config={'PHONE_NUMBER': PiiState.Synthesis},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=True)})
    assert not is_all_digits(response.de_identify_results[0].new_text)
        
    response = textual.redact(
        "My number is qwerasdfzxcvqwerasdfqwer",
        generator_default=PiiState.Off,
        generator_config={'PHONE_NUMBER': PiiState.Synthesis},
        label_allow_lists={'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']},
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=False)})
    assert not is_all_digits(response.de_identify_results[0].new_text)

def test_date_time(textual: TextualNer, server_version: str):
    response = textual.redact(
        "I have an appointment on 08xx07xx2024.",
        generator_default=PiiState.Off,
        generator_config={'DATE_TIME':PiiState.Synthesis},
        label_allow_lists={'DATE_TIME':['08xx07xx2024']},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(additional_date_formats=['dd\'xx\'MM\'xx\'yyyy'])})
    output = response.de_identify_results[0].new_text
    match = re.match(r'(\d{2})xx(\d{2})xx(\d{4})', output)
    assert int(match.group(1))>=1 and int(match.group(1))<=15
    assert match.group(2)=='07'
    assert match.group(3)=='2024'

    response = textual.redact("I have an appointment on 08-13-2024. That is 3 days before 08-16-24.  It is 7 days before 08-20-2024 and a month before 09-13-2024.",
        generator_default=PiiState.Off,
        generator_config={'DATE_TIME':PiiState.Synthesis},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(apply_constant_shift_to_document=True)})

    d1 = datetime.strptime(response.de_identify_results[0].new_text, '%m-%d-%Y').date()
    d2 = datetime.strptime(response.de_identify_results[1].new_text, '%m-%d-%y').date()
    d3 = datetime.strptime(response.de_identify_results[2].new_text, '%m-%d-%Y').date()
    d4 = datetime.strptime(response.de_identify_results[3].new_text, '%m-%d-%Y').date()

    assert (d2-d1).days == 3
    assert (d3-d1).days == 7
    assert (d4-d1).days == 31

    if server_version == 'PRAPP' or server_version == 'DEVELOPMENT' or int(server_version)>=290:
        metadata = {'DATE_TIME': DateTimeGeneratorMetadata(metadata=TimestampShiftMetadata(left_shift_in_days=-10000, right_shift_in_days=10000))}
    else:
        metadata = {'DATE_TIME': DateTimeGeneratorMetadata(metadata=TimestampShiftMetadata(time_stamp_shift_in_days=10000))}

    response = textual.redact("I have an appointment on 08-13-2024",
        generator_default=PiiState.Off,
        generator_config={'DATE_TIME':PiiState.Synthesis},
        generator_metadata=metadata)
    d = datetime.strptime(response.de_identify_results[0].new_text, '%m-%d-%Y').date()
    assert d.year > 2024

def test_age(textual: TextualNer):
    response = textual.redact("I am 38 years old", generator_default=PiiState.Off,generator_config={'PERSON_AGE':PiiState.Synthesis})
    assert int(response.de_identify_results[0].new_text) >= 31 and int(response.de_identify_results[0].new_text) <= 45

    response = textual.redact("I am 38 years old",
        generator_default=PiiState.Off,
        generator_config={'PERSON_AGE':PiiState.Synthesis},
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(metadata=AgeShiftMetadata(age_shift_in_years=500))})
    assert int(response.de_identify_results[0].new_text) > 45

    response = textual.redact("I am 97 years old",
        generator_default=PiiState.Off,
        generator_config={'PERSON_AGE':PiiState.Synthesis},
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(metadata=AgeShiftMetadata(age_shift_in_years=5))})
    assert int(response.de_identify_results[0].new_text) >= 90 and int(response.de_identify_results[0].new_text) <= 104

def is_all_digits(val: str):
    for c in val:
        if not c.isdigit():
            return False
    return True