import os
import boto3

from config.settings import (
    AWS_PROFILE
)


def get_account_session():

    os.environ["AWS_PROFILE"] = (
        AWS_PROFILE
    )

    return boto3.Session()