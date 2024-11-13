from enum import Enum


class AwsCredentialsSource(str, Enum):
    user_provided = ("UserProvided",)
    from_environment = ("FromEnvironment",)
