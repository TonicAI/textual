import io
import uuid
import time
import random

from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.enums.pii_type import PiiType
from tonic_textual.redact_api import TextualNer

def test_get_occurences(textual: TextualNer):
    ds_name = str(uuid.uuid4()) + 'test-occurences'
    ds = textual.create_dataset(ds_name)
    ds.add_file(file_name = 'file1.txt', file = create_file_stream("My name is John Smith. I live in Atlanta."))
    ds.add_file(file_name = 'file2.txt', file = create_file_stream("My name is Sally. I live in Georgia."))

    retries = 0
    processed_files = []
    while retries<60:
        
        processed_files =  ds.get_processed_files(refetch=True)

        if(len(processed_files)==2):
            break

        time.sleep(2)
        retries=retries+1

    assert len(processed_files)==2, "Failed to process files"

    file1: DatasetFile = list(filter(lambda x: x.name=='file1.txt', processed_files))[0]
    file2: DatasetFile = list(filter(lambda x: x.name=='file2.txt', processed_files))[0]

    file1_entities = file1.get_entities()
    file2_entities = file2.get_entities()

    assert len(file1_entities['NAME_GIVEN'])==1, 'unexpected name_given in file1'
    assert file1_entities['NAME_GIVEN'][0]['entity']=='John'
    
    assert len(file1_entities['NAME_FAMILY'])==1, 'unexpected name_family in file1'
    assert file1_entities['NAME_FAMILY'][0]['entity']=='Smith'

    assert len(file1_entities['LOCATION_CITY'])==1, 'unexpected location_city in file1'
    assert file1_entities['LOCATION_CITY'][0]['entity']=='Atlanta'

    assert len(file2_entities['NAME_GIVEN'])==1, 'unexpected name_give in file2'
    assert file2_entities['NAME_GIVEN'][0]['entity']=='Sally'

    assert len(file2_entities['LOCATION_STATE'])==1, 'unexpected location_state in file2'
    assert file2_entities['LOCATION_STATE'][0]['entity']=='Georgia'

def test_occurences_pagination(textual: TextualNer):
    #we fetch 1000 records at a time per entity, so lets create a file with 1050 numeric values
    random_numbers = [random.randint(0, 1000) for _ in range(1050)]
    lines = ['The number is ' + str(r) for r in random_numbers]
    document = '\n'.join(lines)

    ds_name = str(uuid.uuid4()) + 'test-occurences-pagination'
    ds = textual.create_dataset(ds_name)
    ds.add_file(file_name = 'file.txt', file = create_file_stream(document))

    retries = 0
    processed_files = []
    while retries<60:
        
        processed_files =  ds.get_processed_files(refetch=True)

        if(len(processed_files)==2):
            break

        time.sleep(2)
        retries=retries+1

    assert len(processed_files)==1, "Failed to process files"

    file: DatasetFile = list(filter(lambda x: x.name=='file.txt', processed_files))[0]

    entities = file.get_entities(PiiType.NUMERIC_VALUE)
    occurrences = entities['NUMERIC_VALUE']

    assert len(occurrences)==1050, 'failed pagination'

def create_file_stream(txt: str) -> io.BytesIO:
    return io.BytesIO(txt.encode('utf-8'))
