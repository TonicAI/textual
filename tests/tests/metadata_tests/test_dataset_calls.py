import io
from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.date_time_generator_metadata import DateTimeGeneratorMetadata
from tonic_textual.classes.generator_metadata.hipaa_address_generator_metadata import HipaaAddressGeneratorMetadata
from tonic_textual.classes.generator_metadata.name_generator_metadata import NameGeneratorMetadata
from tonic_textual.classes.generator_metadata.numeric_value_generator_metadata import NumericValueGeneratorMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.generator_metadata.phone_number_generator_metadata import PhoneNumberGeneratorMetadata
from tonic_textual.classes.generator_metadata.timestamp_shift_metadata import TimestampShiftMetadata
from tonic_textual.enums.pii_type import PiiType
from tonic_textual.redact_api import TextualNer
import uuid

def test_names_on_dataset(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'name-metadata')
    file = ds.add_file(file_name = 'test.txt', file = create_file_stream("My name is Adam. Again, my name is adam."))
    
    ds.edit(generator_config={'NAME_GIVEN':'Synthesis'})
    output_case_insensitive = get_file_content(file.download())    
    

    ds.edit(generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(is_consistency_case_sensitive=True)})    
    output_case_sensitive = get_file_content(file.download())
    
    assert output_case_insensitive != output_case_sensitive


    ds.edit(generator_config={'NAME_GIVEN':'Synthesis'}, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=False)})
    not_preserved_output = get_file_content(file.download())

    ds.edit(generator_config={'NAME_GIVEN':'Synthesis'}, generator_metadata={'NAME_GIVEN':NameGeneratorMetadata(preserve_gender=True)})
    preserved_output = get_file_content(file.download())

    assert not_preserved_output != preserved_output

    textual.delete_dataset(ds.name)

def test_hipaa_address_on_dataset(textual: TextualNer):
    ds = textual.create_dataset(str(uuid.uuid4())+'hipaa-metadata')

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I live in Atlanta, GA."))
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I live in Atlanta, GA. 30305."))
    file3 = ds.add_file(file_name = 'test3.txt', file = create_file_stream("I live in AtLaNtA"))

    ds.edit(generator_config={'LOCATION_STATE':'Synthesis', 'LOCATION_CITY':'Off'})
    output = get_file_content(file1.download())
    assert output.strip() == 'I live in Atlanta, GA.', "HIPAA Address generator doesn't synthesize states"
    
    ds.edit(generator_config={'LOCATION_STATE':'Synthesis', 'LOCATION_CITY':'Off'}, generator_metadata={'LOCATION_STATE': HipaaAddressGeneratorMetadata(use_non_hipaa_address_generator=True)})
    output = get_file_content(file1.download())
    assert output.strip() == 'I live in Atlanta, MASSACHUSETTS.', "non-HIPAA Address generator does synthesize states"

    ds.edit(generator_config={'LOCATION_ZIP':'Synthesis', 'LOCATION_STATE':'Off', 'LOCATION_CITY':'Off'})
    output = get_file_content(file2.download())    
    assert output.strip() == 'I live in Atlanta, GA. 30342.', "by default, we replace last 2 of zip"

    ds.edit(generator_config={'LOCATION_ZIP':'Synthesis', 'LOCATION_STATE':'Off', 'LOCATION_CITY':'Off'}, generator_metadata={'LOCATION_ZIP': HipaaAddressGeneratorMetadata(replace_truncated_zeros_in_zip_code=False)})
    output = get_file_content(file2.download())
    assert output.strip() == 'I live in Atlanta, GA. 30300.', "we replace last 2 of zip with zeros"

    ds.edit(generator_config={'LOCATION_CITY':'Synthesis'},  generator_metadata={'LOCATION_CITY': HipaaAddressGeneratorMetadata(realistic_synthetic_values=False)})
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

    gc = {piiType: 'Off' for piiType in PiiType}
    gc['NUMERIC_VALUE'] = 'Synthesis'

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
    gc = {piiType: 'Off' for piiType in PiiType}
    gc['PHONE_NUMBER'] = 'Synthesis'

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

def test_date_time(textual: TextualNer):

    ds = textual.create_dataset(str(uuid.uuid4())+'phone-metadata')
    gc = {piiType: 'Off' for piiType in PiiType}
    gc['DATE_TIME'] = 'Synthesis'

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I have an appointment on 08xx07xx2024."))
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I have an appointment on 08-13-2024. That is 3 days before 08-16-24.  It is 7 days before 08-20-2024 and a month before 09-13-2024."))
    file3 = ds.add_file(file_name = 'test3.txt', file = create_file_stream("I have an appointment on 08-13-2024"))
    
    ds.edit(
        generator_config=gc,
        label_allow_lists={'DATE_TIME':['08xx07xx2024']},
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(additional_date_formats=['dd\'xx\'MM\'xx\'yyyy'])})
    output = get_file_content(file1.download())    
    assert '06xx07xx2024' in output

    
    ds.edit(
        generator_config=gc,
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(apply_constant_shift_to_document=True)})
    output = get_file_content(file2.download())
    assert output.strip() == 'I have an appointment on 08-10-2024. That is 3 days before 08-13-24.  It is 7 days before 08-17-2024 and a month before 09-10-2024.'

    ds.edit(
        generator_config=gc,
        generator_metadata={'DATE_TIME': DateTimeGeneratorMetadata(timestamp_shift_metadata=TimestampShiftMetadata(timestamp_shift_in_days=10000))})
    output = get_file_content(file3.download())
    assert output.strip() == 'I have an appointment on 09-11-2030'

    textual.delete_dataset(ds.name)

def test_age(textual: TextualNer):

    ds = textual.create_dataset(str(uuid.uuid4())+'phone-metadata')
    gc = {piiType: 'Off' for piiType in PiiType}
    gc['PERSON_AGE'] = 'Synthesis'

    file1 = ds.add_file(file_name = 'test1.txt', file = create_file_stream("I am 38 years old"))    
    file2 = ds.add_file(file_name = 'test2.txt', file = create_file_stream("I am 97 years old"))

    ds.edit(generator_config=gc)
    output = get_file_content(file1.download())
    assert output.strip() == 'I am 44 years old'

    ds.edit(
        generator_config=gc,
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(age_shift_metadata=AgeShiftMetadata(age_shift_in_years=500))})
    output = get_file_content(file1.download())
    assert output.strip() == 'I am 536 years old'

    ds.edit(
        generator_config=gc,
        generator_metadata={'PERSON_AGE': PersonAgeGeneratorMetadata(age_shift_metadata=AgeShiftMetadata(age_shift_in_years=5))})
    output = get_file_content(file2.download())    
    assert output.strip() == 'I am 92 years old'

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