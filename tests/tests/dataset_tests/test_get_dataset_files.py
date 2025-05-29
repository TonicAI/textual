from tonic_textual.redact_api import TextualNer

import uuid
import io
import time

def test_processed_files_get_updated(textual: TextualNer):
    ds_name = str(uuid.uuid4()) + 'test-processed-files'
    ds = textual.create_dataset(ds_name)
    ds.add_file(file_name = 'test.txt', file = create_file_stream("My name is Adam. Again, my name is adam."))

    assert len(ds.files)==1, 'adding file updates list of dataset files'    
    assert len(ds.get_queued_files(refetch=False))==1

    counter = 0
    success = False
    while counter < 60:
        if len(ds.get_processed_files())==1:
            success = True
            break
        time.sleep(1)
        counter=counter+1
    assert success, "file should be processed and updated due to refetch"

def test_processed_failed_files(textual: TextualNer):
    ds_name = str(uuid.uuid4())+'test-processed-files'
    ds = textual.create_dataset(ds_name)
    #invalid pdf
    ds.add_file(file_name = 'test.pdf', file = create_file_stream("My name is Adam. Again, my name is adam."))

    counter = 0
    success = False
    while counter<60:
        if len(ds.get_failed_files())==1:
            success=True
            break
        time.sleep(1)
        counter=counter+1
    assert success, "file should fail to process"

def create_file_stream(txt: str) -> io.BytesIO:
    return io.BytesIO(txt.encode('utf-8'))