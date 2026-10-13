import io
import uuid
import time
import random

from tonic_textual.classes.datasetfile import DatasetFile
from tonic_textual.enums.pii_type import PiiType
from tonic_textual.redact_api import TextualNer

def test_get_occurences(textual: TextualNer, created_datasets):
    ds_name = str(uuid.uuid4()) + 'test-occurences'
    ds = textual.create_dataset(ds_name)
    created_datasets.append(ds_name)
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

    expected_pii_types = [
        PiiType.NAME_GIVEN,
        PiiType.NAME_FAMILY,
        PiiType.LOCATION_CITY,
        PiiType.LOCATION_STATE,
    ]
    file1_entities = file1.get_entities(expected_pii_types)
    file2_entities = file2.get_entities(expected_pii_types)

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

def test_occurences_pagination(textual: TextualNer, created_datasets):
    #we fetch 5 records at a time per entity, so lets create a file with 12 numeric values
    random_numbers = random.sample(range(1001), 30)
    lines = ['The number is ' + str(r) for r in random_numbers]
    document = '\n'.join(lines)

    ds_name = str(uuid.uuid4()) + 'test-occurences-pagination'
    ds = textual.create_dataset(ds_name)
    created_datasets.append(ds_name)
    ds.add_file(file_name = 'file.txt', file = create_file_stream(document))

    retries = 0
    processed_files = []
    while retries<60:
        
        processed_files =  ds.get_processed_files(refetch=True)

        if(len(processed_files)==1):
            break

        time.sleep(2)
        retries=retries+1

    assert len(processed_files)==1, "Failed to process files"

    file: DatasetFile = list(filter(lambda x: x.name=='file.txt', processed_files))[0]
    # Which label a bare number gets (NUMERIC_VALUE, CREDIT_CARD, ...) depends on the model, so
    # compare paginated results against a single unpaginated fetch rather than a fixed label count.
    file._pii_occurence_file_limit=5
    paged = file.get_entities()
    paged_mixed = file.get_entities([PiiType.NUMERIC_VALUE, 'NAME_FAMILY']) #we add a string value to make sure we support both str and piitype instances

    file._pii_occurence_file_limit=1000
    unpaged = file.get_entities()
    unpaged_mixed = file.get_entities([PiiType.NUMERIC_VALUE, 'NAME_FAMILY'])

    assert occurrence_keys(paged) == occurrence_keys(unpaged), 'failed pagination'
    assert occurrence_keys(paged_mixed) == occurrence_keys(unpaged_mixed), 'failed pagination'

    found = {o['entity'] for occurrences in paged.values() for o in occurrences}
    assert {str(r) for r in random_numbers} <= found, 'failed pagination'

def occurrence_keys(entities):
    return sorted((pii_type, o['entity'], o['head'], o['tail']) for pii_type, occurrences in entities.items() for o in occurrences)

def create_file_stream(txt: str) -> io.BytesIO:
    return io.BytesIO(txt.encode('utf-8'))
