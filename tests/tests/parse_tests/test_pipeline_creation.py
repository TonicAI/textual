import os
import time
import uuid

from tonic_textual.classes.pipeline_aws_credential import PipelineAwsCredential
from tonic_textual.classes.pipeline_azure_credential import PipelineAzureCredential
from tonic_textual.classes.pipeline_databricks_credential import (
    PipelineDatabricksCredential,
)

from azure.storage.blob import BlobClient


# test just checks that exception is not thrown
def test_s3_pipelines(textual_parse):
    for synth in [False, True]:
        for cred_source in ["user_provided", "from_environment"]:
            creds = (
                PipelineAwsCredential(
                    aws_access_key_id=os.environ["S3_UPLOAD_ACCESS_KEY"],
                    aws_region=os.environ["AWS_DEFAULT_REGION"],
                    aws_secret_access_key=os.environ["S3_UPLOAD_SECRET_KEY"],
                )
                if cred_source == "user_provided"
                else None
            )
            textual_parse.create_s3_pipeline(
                f"aws_{cred_source}_{str(synth)}_{uuid.uuid4()}",
                aws_credentials_source=cred_source,
                synthesize_files=synth,
                credentials=creds,
            )

# test just checks that exception is not thrown
def test_s3_pipeline_with_kms(textual_parse):
    for synth in [False, True]:
        for cred_source in ["user_provided", "from_environment"]:
            creds = (
                PipelineAwsCredential(
                    aws_access_key_id=os.environ["S3_UPLOAD_ACCESS_KEY"],
                    aws_region=os.environ["AWS_DEFAULT_REGION"],
                    aws_secret_access_key=os.environ["S3_UPLOAD_SECRET_KEY"],
                )
                if cred_source == "user_provided"
                else None
            )
            textual_parse.create_s3_pipeline(
                f"aws_{cred_source}_{str(synth)}_{uuid.uuid4()}",
                aws_credentials_source=cred_source,
                synthesize_files=synth,
                credentials=creds,
                kms_key_arn=os.environ["S3_KMS_KEY_ARN"]
            )


def test_local_pipelines(textual_parse):
    for synth in [False, True]:
        textual_parse.create_local_pipeline(
            f"local_{str(synth)}", synthesize_files=synth
        )


def test_azure_pipelines(textual_parse):
    for synth in [False, True]:
        textual_parse.create_azure_pipeline(
            f"azure_{str(synth)}_{uuid.uuid4()}",
            credentials=PipelineAzureCredential(
                account_name=os.environ["AZURE_ACCOUNT_NAME"],
                account_key=os.environ["AZURE_ACCOUNT_KEY"],
            ),
            synthesize_files=synth,
        )


def test_databricks_pipelines(textual_parse):
    for synth in [False, True]:
        textual_parse.create_databricks_pipeline(
            f"databricks_{str(synth)}_{uuid.uuid4()}",
            credentials=PipelineDatabricksCredential(
                url=os.environ["DATABRICKS_URL"],
                access_token=os.environ["DATABRICKS_ACCESS_TOKEN"],
            ),
            synthesize_files=synth,
        )


def test_configuring_s3_pipeline(textual_parse, s3_boto_client):
    input_bucket = os.environ["S3_UPLOAD_BUCKET"]
    output_bucket = os.environ["S3_OUTPUT_BUCKET"]
    # Create pipeline after files are uploaded
    creds = PipelineAwsCredential(
        aws_access_key_id=os.environ["S3_UPLOAD_ACCESS_KEY"],
        aws_region=os.environ["AWS_DEFAULT_REGION"],
        aws_secret_access_key=os.environ["S3_UPLOAD_SECRET_KEY"],
    )
    s3_pipeline = textual_parse.create_s3_pipeline(
        f"aws_configuration_test_{uuid.uuid4()}", credentials=creds
    )

    s3_pipeline.set_synthesize_files(True)
    s3_pipeline.set_output_location(output_bucket)
    s3_pipeline.add_files(input_bucket, ["simple_file.txt"])
    s3_pipeline.add_prefixes(input_bucket, ["chat_transcript.txt"])

    job_id = s3_pipeline.run()

    max_retries = 60 * 15 # 15 minutes
    while max_retries > 0:
        runs = s3_pipeline.get_runs()
        successful_runs = list(filter(lambda r: r.status == "Completed", runs))
        if len(successful_runs) > 0:
            print("Found successful run.")
            break
        print(f"Runs:{len(runs)}; Successful:{len(successful_runs)}")
        time.sleep(1)
        max_retries -= 1

    assert max_retries > 0, "No successful runs found."

    # check that we process the expected files
    files = [file for file in s3_pipeline.enumerate_files()]
    assert len(files) == 2

    file_names = set([file.file.fileName for file in files])
    assert "simple_file.txt" in file_names
    assert "chat_transcript.txt" in file_names

    # check that synthesized file is found in expected location in s3
    s3_boto_client.get_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/simple_file.txt"
    )
    s3_boto_client.delete_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/simple_file.txt"
    )

    s3_boto_client.get_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/chat_transcript.txt"
    )
    s3_boto_client.delete_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/chat_transcript.txt"
    )

    # check that parsed json is found in expected location in s3
    s3_boto_client.get_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/simple_file_txt_parsed.json"
    )
    s3_boto_client.delete_object(
        Bucket=output_bucket, Key=f"{job_id}/{input_bucket}/simple_file_txt_parsed.json"
    )
    s3_boto_client.get_object(
        Bucket=output_bucket,
        Key=f"{job_id}/{input_bucket}/chat_transcript_txt_parsed.json",
    )
    s3_boto_client.delete_object(
        Bucket=output_bucket,
        Key=f"{job_id}/{input_bucket}/chat_transcript_txt_parsed.json",
    )

    textual_parse.delete_pipeline(s3_pipeline.id)


def test_configuring_azure_pipeline(textual_parse):
    input_container = "integration-tests-input"
    output_container = "integration-tests-output"
    creds = PipelineAzureCredential(
        account_name=os.environ["AZURE_ACCOUNT_NAME"],
        account_key=os.environ["AZURE_ACCOUNT_KEY"],
    )
    azure_pipeline = textual_parse.create_azure_pipeline(
        f"azure_{uuid.uuid4()}", credentials=creds
    )
    azure_pipeline.set_synthesize_files(True)
    azure_pipeline.set_output_location(output_container, "sdk")
    azure_pipeline.add_files(input_container, ["fraud.txt", "scientist.txt"])
    azure_pipeline.add_prefixes(input_container, ["biographies"])
    job_id = azure_pipeline.run()

    max_retries = 120
    while max_retries > 0:
        runs = azure_pipeline.get_runs()
        successful_runs = list(filter(lambda r: r.status == "Completed", runs))
        if len(successful_runs) > 0:
            print("Found successful run.")
            break
        print(f"Runs:{len(runs)}; Successful:{len(successful_runs)}")
        time.sleep(1)
        max_retries -= 1

    assert max_retries > 0, "No successful runs found."

    # check that we process the expected files
    files = [file for file in azure_pipeline.enumerate_files()]
    assert len(files) == 3

    file_names = set([file.file.fileName for file in files])
    assert "upload.csv" in file_names
    assert "scientist.txt" in file_names
    assert "fraud.txt" in file_names

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/fraud_txt_parsed.json",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "fraud_txt_parsed.json not found"
    blob.delete_blob()

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/fraud.txt",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "fraud.txt not found"
    blob.delete_blob()

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/scientist_txt_parsed.json",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "scientist_txt_parsed.json not found"
    blob.delete_blob()

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/scientist.txt",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "scientist.txt not found"
    blob.delete_blob()

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/biographies/upload_csv_parsed.json",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "upload_csv_parsed.json not found"
    blob.delete_blob()

    blob = BlobClient(
        account_url=f"https://{os.environ['AZURE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=output_container,
        blob_name=f"sdk/{job_id}/{input_container}/biographies/upload.csv",
        credential=os.environ["AZURE_ACCOUNT_KEY"],
    )
    assert blob.exists(), "upload.csv not found"
    blob.delete_blob()
