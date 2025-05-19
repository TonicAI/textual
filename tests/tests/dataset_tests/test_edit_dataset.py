import pytest
import uuid

from tonic_textual.classes.generator_metadata.age_shift_metadata import AgeShiftMetadata
from tonic_textual.classes.generator_metadata.person_age_generator_metadata import PersonAgeGeneratorMetadata
from tonic_textual.classes.enums.file_redaction_policies import docx_comment_policy, docx_image_policy, docx_table_policy, pdf_signature_policy, pdf_synth_mode_policy
from tonic_textual.classes.tonic_exception import DatasetNameAlreadyExists
from tonic_textual.enums.pii_state import PiiState
from tonic_textual.enums.pii_type import PiiType


def test_edit_dataset(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    name1 = str(uuid.uuid4())
    name2 = str(uuid.uuid4())
    dataset = textual.create_dataset(name1)

    dataset.edit(name=name2, label_allow_lists={"ORGANIZATION": ["that"]})

    assert dataset.name == name2


def test_edit_dataset_with_copied_metadata_and_config(textual):
    name1 = str(uuid.uuid4())
    name2 = str(uuid.uuid4())

    dataset1 = textual.create_dataset(name1)
    dataset2 = textual.create_dataset(name2)

    outbound_person_age_metadata = PersonAgeGeneratorMetadata(
        scramble_unrecognized_dates=False,
        metadata=AgeShiftMetadata(age_shift_in_years=10)
    )

    dataset1.edit(
        generator_config={PiiType.LOCATION_COMPLETE_ADDRESS.name:PiiState.Redaction},
        generator_metadata={PiiType.PERSON_AGE:outbound_person_age_metadata}
    )

    dataset2.edit(
        generator_config=dataset1.generator_config,
        generator_metadata=dataset1.generator_metadata
    )

    assert dataset2.generator_config[PiiType.LOCATION_COMPLETE_ADDRESS.name] == PiiState.Redaction
    assert dataset2.generator_metadata[PiiType.PERSON_AGE.name].metadata.age_shift_in_years == 10


def test_edit_datasetname_to_conflict(textual):
    # name must be unique. if you already have a dataset, fetch it using get_dataset()
    name1 = str(uuid.uuid4())
    name2 = str(uuid.uuid4())
    textual.create_dataset(name1)
    dataset2 = textual.create_dataset(name2)

    with pytest.raises(DatasetNameAlreadyExists):
        dataset2.edit(name=name1)

def test_policies(textual):

    name = 'policy-edit-'+str(uuid.uuid4())
    ds = textual.create_dataset(name)

    assert ds.docx_image_policy==docx_image_policy.redact
    assert ds.docx_comment_policy==docx_comment_policy.remove
    assert ds.docx_table_policy==docx_table_policy.redact
    assert ds.pdf_signature_policy==pdf_signature_policy.redact
    assert ds.pdf_synth_mode_policy==pdf_synth_mode_policy.V1

    ds.edit(
        pdf_synth_mode_policy=pdf_synth_mode_policy.V2,
        docx_comment_policy_name=docx_comment_policy.ignore,
        docx_image_policy_name=docx_image_policy.ignore,
        docx_table_policy_name=docx_table_policy.remove,
        pdf_signature_policy_name=pdf_signature_policy.ignore)

    assert ds.docx_image_policy==docx_image_policy.ignore
    assert ds.docx_comment_policy==docx_comment_policy.ignore
    assert ds.docx_table_policy==docx_table_policy.remove
    assert ds.pdf_signature_policy==pdf_signature_policy.ignore
    assert ds.pdf_synth_mode_policy==pdf_synth_mode_policy.V2

    ds = textual.get_dataset(name)

    assert ds.docx_image_policy==docx_image_policy.ignore
    assert ds.docx_comment_policy==docx_comment_policy.ignore
    assert ds.docx_table_policy==docx_table_policy.remove
    assert ds.pdf_signature_policy==pdf_signature_policy.ignore
    assert ds.pdf_synth_mode_policy==pdf_synth_mode_policy.V2