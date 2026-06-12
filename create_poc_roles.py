import json

import boto3
from botocore.exceptions import ClientError

from config.settings import AWS_PROFILE


session = boto3.Session(
    profile_name=AWS_PROFILE
)

iam = session.client("iam")


TRUST_EC2 = {
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


ROLES = [
    {
        "name": "CK-Test-Assessment-Role",
        "path": "/",
        "description": "Assessment role",
        "max_session_duration": 3600,
        "managed_policies": [
            "arn:aws:iam::aws:policy/ReadOnlyAccess"
        ],
        "inline_policies": {},
        "instance_profile": None
    },
    {
        "name": "CK-Test-Tuner-Role",
        "path": "/application/",
        "description": "",
        "max_session_duration": 3600,
        "managed_policies": [
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        ],
        "inline_policies": {
            "TunerInlinePolicy": {
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
        },
        "instance_profile": None
    },
    {
        "name": "CK-Test-Analytics-BE-Service-Role",
        "path": "/service-role/",
        "description": "Analytics backend",
        "max_session_duration": 7200,
        "managed_policies": [
            "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        ],
        "inline_policies": {},
        "instance_profile": "CK-Test-Analytics-BE-Service-Profile"
    },
    {
        "name": "CK-Test-Analytics-Data-ECS-Service-Role",
        "path": "/service-role/",
        "description": "",
        "max_session_duration": 3600,
        "managed_policies": [],
        "inline_policies": {
            "AnalyticsInlinePolicy": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*"
                    }
                ]
            }
        },
        "instance_profile": None
    },
    {
        "name": "CK-Test-EKS-LoadBalancer-Controller-Role",
        "path": "/",
        "description": "EKS LB Controller",
        "max_session_duration": 43200,
        "managed_policies": [
            "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
        ],
        "inline_policies": {},
        "instance_profile": None
    },
    {
        "name": "CK-Test-CloudFormation-Execution-Role",
        "path": "/service-role/",
        "description": "CloudFormation execution role",
        "max_session_duration": 3600,
        "managed_policies": [
            "arn:aws:iam::aws:policy/AdministratorAccess"
        ],
        "inline_policies": {},
        "instance_profile": None
    },
    {
        "name": "CK-Test-NetworkOne",
        "path": "/application/",
        "description": "",
        "max_session_duration": 14400,
        "managed_policies": [
            "arn:aws:iam::aws:policy/ReadOnlyAccess"
        ],
        "inline_policies": {},
        "instance_profile": None
    },
    {
        "name": "CK-Test-AlmaConnect",
        "path": "/service-role/",
        "description": "Role with everything",
        "max_session_duration": 10800,
        "managed_policies": [
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
            "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
        ],
        "inline_policies": {
            "AlmaInlinePolicy": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:ListQueues"
                        ],
                        "Resource": "*"
                    }
                ]
            }
        },
        "instance_profile": "CK-Test-AlmaConnect-Profile"
    }
]


for role in ROLES:

    role_name = role["name"]

    try:

        iam.create_role(
            RoleName=role_name,
            Path=role["path"],
            Description=role["description"],
            MaxSessionDuration=role["max_session_duration"],
            AssumeRolePolicyDocument=json.dumps(
                TRUST_EC2
            )
        )

        for policy_arn in role["managed_policies"]:

            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )

        for (
            policy_name,
            policy_document
        ) in role["inline_policies"].items():

            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(
                    policy_document
                )
            )

        if role["instance_profile"]:

            profile_name = role[
                "instance_profile"
            ]

            try:

                iam.create_instance_profile(
                    InstanceProfileName=
                    profile_name
                )

            except ClientError as e:

                if (
                    e.response["Error"]["Code"]
                    != "EntityAlreadyExists"
                ):
                    raise

            iam.add_role_to_instance_profile(
                InstanceProfileName=
                profile_name,
                RoleName=role_name
            )

        print(
            f"Created: {role_name}"
        )

    except Exception as e:

        print(
            f"{role_name}: {e}"
        )