import json

import boto3


ACCOUNT_ID = "275595855473"

ROLE_NAME = "poc-ck-test-nonprod-role"


session = boto3.Session()

iam = session.client("iam")


trust_policy = {

    "Version": "2012-10-17",

    "Statement": [

        {

            "Effect": "Allow",

            "Principal": {

                "Service": "ec2.amazonaws.com"

            },

            "Action": "sts:AssumeRole"

        }

    ]
}


inline_policy = {

    "Version": "2012-10-17",

    "Statement": [

        {

            "Effect": "Allow",

            "Action": [

                "s3:ListBucket"

            ],

            "Resource": "*"

        }

    ]
}


try:

    iam.get_role(
        RoleName=ROLE_NAME
    )

    print(
        f"Role already exists: {ROLE_NAME}"
    )

except iam.exceptions.NoSuchEntityException:

    iam.create_role(

        RoleName=ROLE_NAME,

        Description=
        "POC IAM Cleaner NonProd Test Role",

        MaxSessionDuration=3600,

        AssumeRolePolicyDocument=
        json.dumps(trust_policy)
    )

    iam.attach_role_policy(

        RoleName=ROLE_NAME,

        PolicyArn=
        "arn:aws:iam::aws:policy/ReadOnlyAccess"
    )

    iam.attach_role_policy(

        RoleName=ROLE_NAME,

        PolicyArn=
        "arn:aws:iam::aws:policy/IAMReadOnlyAccess"
    )

    iam.put_role_policy(

        RoleName=ROLE_NAME,

        PolicyName=
        "POCInlinePolicy",

        PolicyDocument=
        json.dumps(inline_policy)
    )

    print(
        f"Created: {ROLE_NAME}"
    )

print(
    f"ARN: arn:aws:iam::{ACCOUNT_ID}:role/{ROLE_NAME}"
)