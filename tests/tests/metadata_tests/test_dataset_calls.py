import io
import uuid
import re
from typing import Dict
from datetime import datetime

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import PiiType
from tonic_textual.redact_api import TextualNer

def test_names_on_dataset(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'name-metadata')
    file = ds.add_file(file_name = 'test.txt', file = create_file_stream("My name is Adam. Again, my name is adam."))
    
    ds.edit(generator_config={'NAME_GIVEN':PiiState.Synthesis})
    output_case_insensitive = get_file_content(file.download())    
    

    ds.edit(generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(is_consistency_case_sensitive=True)})    
    output_case_sensitive = get_file_content(file.download())
    
    assert output_case_insensitive != output_case_sensitive


    ds.edit(generator_config={'NAME_GIVEN':PiiState.Synthesis}, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=False)})
    not_preserved_output = get_file_content(file.download())

    ds.edit(generator_config={'NAME_GIVEN':PiiState.Synthesis}, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=True)})
    preserved_output = get_file_content(file.download())

    assert not_preserved_output != preserved_output

    textual.delete_dataset(ds.name)

def test_hipaa_address_on_dataset(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'hipaa-metadata')

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I live in Atlanta, GA."))
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I live in Atlanta, GA. 30305."))
    file3 = ds.add_file(file_name = 'test3.txt', file = create_file_stream("I live in AtLaNtA"))

    ds.edit(generator_config={'LOCATION_STATE':PiiState.Synthesis, 'LOCATION_CITY':PiiState.Off})
    output = get_file_content(file1.download())
    assert output.strip() == 'I live in Atlanta, GA.', "HIPAA Address generator doesn't synthesize states"
    
    ds.edit(generator_config={'LOCATION_STATE':PiiState.Synthesis, 'LOCATION_CITY':PiiState.Off}, generator_metadata={'LOCATION_STATE': HipaaAddressGeneratorMetadata(use_non_hipaa_address_generator=True)})
    output = get_file_content(file1.download()).strip()
    match = re.match('(I live in Atlanta, )(.*)\.', output)
    assert match.group(1) == 'I live in Atlanta, '
    assert match.group(2) != 'GA'

    ds.edit(generator_config={'LOCATION_ZIP':PiiState.Synthesis, 'LOCATION_STATE':PiiState.Off, 'LOCATION_CITY':PiiState.Off})
    output = get_file_content(file2.download()).strip()
    match = re.match('(I live in Atlanta, GA\. )(.*)\.', output)
    assert match.group(1) == 'I live in Atlanta, GA. '
    assert match.group(2) != '30305'

    ds.edit(generator_config={'LOCATION_ZIP':PiiState.Synthesis, 'LOCATION_STATE':PiiState.Off, 'LOCATION_CITY':PiiState.Off}, generator_metadata={'LOCATION_ZIP': HipaaAddressGeneratorMetadata(replace_truncated_zeros_in_zip_code=False)})
    output = get_file_content(file2.download()).strip()
    match = re.match('(I live in Atlanta, GA\. )(.*)\.', output)
    assert match.group(1) == 'I live in Atlanta, GA. '
    assert match.group(2) == '30300'

    ds.edit(generator_config={'LOCATION_CITY':PiiState.Synthesis},  generator_metadata={'LOCATION_CITY': HipaaAddressGeneratorMetadata(realistic_synthetic_values=False)})
    output = get_file_content(file3.download()).strip()
    
    assert output[10].isupper()
    assert output[11].islower()
    assert output[12].isupper()
    assert output[13].islower()
    assert output[14].isupper()
    assert output[15].islower()
    assert output[16].isupper()

    textual.delete_dataset(ds.name)

def test_numeric_value(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'numeric-value-metadata')
    file = ds.add_file(file_name = 'test1.txt', file = create_file_stream("My ID is 123"))

    gc: Dict[PiiType, PiiState] = {piiType: PiiState.Off for piiType in PiiType}
    gc[PiiType.NUMERIC_VALUE] = PiiState.Synthesis

    ds.edit(generator_config=gc)
    output = get_file_content(file.download())
    assert len(output.strip()[9:]) == 3 and output.strip()[9:] != '123'

    ds.edit(generator_config=gc, generator_metadata={'NUMERIC_VALUE':NumericValueGeneratorMetadata(use_oracle_integer_pk_generator=True)})
    output = get_file_content(file.download())
    assert len(output) > 10

    textual.delete_dataset(ds.name)
    
def test_phone_number(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'phone-metadata')
    file = ds.add_file(file_name = 'test1.txt', file = create_file_stream( "My number is qwerasdfzxcvqwerasdfqwer"))

    allow_list = {'PHONE_NUMBER':['qwerasdfzxcvqwerasdfqwer']}
    gc: Dict[PiiType, PiiState] = {piiType: PiiState.Off for piiType in PiiType}
    gc[PiiType.PHONE_NUMBER] = PiiState.Synthesis

    ds.edit(
        generator_config=gc,
        label_allow_lists=allow_list,
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=True)})
    output = get_file_content(file.download())
    assert is_all_digits(output[13:].strip())

    ds.edit(
        generator_config=gc,
        label_allow_lists=allow_list,
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=True, use_us_phone_number_generator=False)})
    output = get_file_content(file.download())
    assert not is_all_digits(output[13:].strip())

    ds.edit(
        generator_config=gc,
        label_allow_lists=allow_list,
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=True)})
    output = get_file_content(file.download())
    assert not is_all_digits(output[13:].strip())    

    ds.edit(
        generator_config=gc,
        label_allow_lists=allow_list,
        generator_metadata={'PHONE_NUMBER': PhoneNumberGeneratorMetadata(replace_invalid_numbers=False, use_us_phone_number_generator=False)})
    output = get_file_content(file.download())
    assert not is_all_digits(output[13:].strip())

    textual.delete_dataset(ds.name)

def test_date_time(textual: TextualNer, server_version: str):

    ds = textual.create_dataset(str(uuid.uuid4())+'phone-metadata')
    gc = {piiType: PiiState.Off for piiType in PiiType}
    gc[PiiType.DATE_TIME] = PiiState.Synthesis

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I have an appointment on 08xx07xx2024."))
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I have an appointment on 08-13-2024. That is 3 days before 08-16-24.  It is 7 days before 08-20-2024 and a month before 09-13-2024."))
    file3 = ds.add_file(file_name = 'test3.txt', file = create_file_stream("I have an appointment on 08-13-2024"))
    
    ds.edit(
        generator_config=gc,
        label_allow_lists={'DATE_TIME':['08xx07xx2024']},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(additional_date_formats=['dd\'xx\'MM\'xx\'yyyy'])})
    output = get_file_content(file1.download()).strip()

    match = re.match(r'.*(\d{2})xx(\d{2})xx(\d{4}).*', output)
    assert int(match.group(1))>=1 and int(match.group(1))<=15
    assert match.group(2)=='07'
    assert match.group(3)=='2024'
    
    ds.edit(
        generator_config=gc,
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(apply_constant_shift_to_document=True)})
    output = get_file_content(file2.download()).strip()

    date_match = re.match(r'.*(\d{2}\-\d{2}\-\d{4}).*(\d{2}\-\d{2}\-\d{2}).*(\d{2}\-\d{2}\-\d{4}).*(\d{2}\-\d{2}\-\d{4}).*', output)
    first_date = date_match.group(1)
    second_date = date_match.group(2)
    third_date = date_match.group(3)
    fourth_date = date_match.group(4)  

    d1 = datetime.strptime(first_date, '%m-%d-%Y').date()
    d2 = datetime.strptime(second_date, '%m-%d-%y').date()
    d3 = datetime.strptime(third_date, '%m-%d-%Y').date()
    d4 = datetime.strptime(fourth_date, '%m-%d-%Y').date()

    assert (d2-d1).days == 3
    assert (d3-d1).days == 7
    assert (d4-d1).days == 31

    if server_version == 'PRAPP' or int(server_version)>=285:
        metadata = {'DATE_TIME': DateTimeGeneratorMetadata(timestamp_shift_metadata=TimestampShiftMetadata(left_shift_in_days=-10000, right_shift_in_days=10000))}
    else:
        metadata = {'DATE_TIME': DateTimeGeneratorMetadata(timestamp_shift_metadata=TimestampShiftMetadata(time_stamp_shift_in_days=10000))}

    ds.edit(
        generator_config=gc,
        generator_metadata=metadata)
    output = get_file_content(file3.download()).strip()
    
    match = re.match(r'.*(\d{2}\-\d{2}\-\d{4}).*', output)
    d1 = datetime.strptime(match.group(1), '%m-%d-%Y').date()
    assert d1.year > 2024

    textual.delete_dataset(ds.name)

def test_age(textual: TextualNer):

    ds = textual.create_dataset(str(uuid.uuid4())+'phone-metadata')
    gc = {piiType: PiiState.Off for piiType in PiiType}
    gc['PERSON_AGE'] = PiiState.Synthesis

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I am 38 years old"))    
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I am 97 years old"))

    ds.edit(generator_config=gc)
    output = get_file_content(file1.download()).strip()
    match = re.match(r'.*\s(\d+).*', output)
    age = match.group(1)
    assert int(age) >= 31 and int(age) <= 45

    ds.edit(
        generator_config=gc,
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(metadata=AgeShiftMetadata(age_shift_in_years=1000))})
    output = get_file_content(file1.download()).strip()        
    match = re.match(r'.*\s(\d+).*', output)
    age = match.group(1)
    assert int(age) > 45

    ds.edit(
        generator_config=gc,
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(metadata=AgeShiftMetadata(age_shift_in_years=5))})
    output = get_file_content(file2.download()).strip()        
    match = re.match(r'.*\s(\d+).*', output)
    age = match.group(1)

    assert int(age) >= 90 and int(age) <= 104

    textual.delete_dataset(ds.name)

def get_file_content(file) -> str:
    return file.decode('utf-8')

def create_file_stream(txt: str) -> io.BytesIO:
    return io.BytesIO(txt.encode('utf-8'))

def is_all_digits(val: str):
    for c in val:
        if not c.isdigit():
            return False
    return True