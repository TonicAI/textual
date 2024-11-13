from typing import Optional


class PipelineAwsCredential(dict):
    """Class to represent AWS credentials used to create an Amazon S3 pipeline.

    Parameters
    ----------
    aws_access_key_id: str
        The AWS access key ID. The access key ID should have permissions on the S3 buckets that you plan to read data from and write data to.

    aws_secret_access_key: str
        The AWS secret access key. The secret access key should have permissions on the S3 buckets that you plan to read data from and write data to.

    aws_region: str
        The AWS region

    aws_session_token: Optional[str]
        An optional AWS session token. Only needed if required by your IAM credentials.
    """

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
        aws_session_token: Optional[str] = None,
    ):
        self.aws_access_key = aws_access_key_id
        self.aws_secret_key = aws_secret_access_key
        self.aws_region = aws_region
        self.aws_session_token = aws_session_token

        dict.__init__(
            self,
            accessKey=aws_access_key_id,
            secretKey=aws_secret_access_key,
            region=aws_region,
            sessionToken=aws_session_token,
        )

    def to_dict(self):
        return {
            "accessKey": self.aws_access_key,
            "secretKey": self.aws_secret_key,
            "region": self.aws_region,
            "sessionToken": self.aws_session_token,
        }
