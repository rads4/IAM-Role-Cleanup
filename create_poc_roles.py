import json

import boto3


def get_available_profiles():

    session = boto3.Session()

    return sorted(
        session.available_profiles
    )


def select_profile():

    profiles = (
        get_available_profiles()
    )

    if not profiles:

        raise Exception(
            "No AWS profiles found"
        )

    print(
        "\nAvailable AWS Profiles:\n"
    )

    for index, profile in enumerate(
        profiles,
        start=1
    ):

        print(
            f"{index}. {profile}"
        )

    while True:

        choice = input(
            "\nSelect Profile: "
        ).strip()

        try:

            return profiles[
                int(choice) - 1
            ]

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection"
            )


def main():

    profile_name = (
        select_profile()
    )

    session = boto3.Session(
        profile_name=profile_name
    )

    iam = session.client(
        "iam"
    )

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service":
                    "ec2.amazonaws.com"
                },
                "Action":
                "sts:AssumeRole"
            }
        ]
    }

    roles = [

        {
            "RoleName":
            "CK-Test-Assessment-Role",

            "Description":
            "Assessment service role",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [
                "arn:aws:iam::aws:policy/ReadOnlyAccess"
            ],

            "InlinePolicies": {}
        },

        {
            "RoleName":
            "CK-Test-Tuner-Role",

            "Description":
            "Tuner service role",

            "MaxSessionDuration":
            7200,

            "ManagedPolicies": [
                "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
            ],

            "InlinePolicies": {
                "TunerInlinePolicy": {
                    "Version":
                    "2012-10-17",
                    "Statement": [
                        {
                            "Effect":
                            "Allow",
                            "Action":
                            [
                                "s3:ListBucket"
                            ],
                            "Resource":
                            "*"
                        }
                    ]
                }
            }
        },

        {
            "RoleName":
            "CK-Test-Analytics-BE-Service-Role",

            "Description":
            "",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [],

            "InlinePolicies": {}
        },

        {
            "RoleName":
            "CK-Test-Analytics-Data-ECS-Service-Role",

            "Description":
            "",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [
                "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
            ],

            "InlinePolicies": {}
        },

        {
            "RoleName":
            "CK-Test-EKS-LoadBalancer-Controller-Role",

            "Description":
            "Load balancer role",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [],

            "InlinePolicies": {
                "LoadBalancerPolicy": {
                    "Version":
                    "2012-10-17",
                    "Statement": [
                        {
                            "Effect":
                            "Allow",
                            "Action":
                            [
                                "ec2:Describe*"
                            ],
                            "Resource":
                            "*"
                        }
                    ]
                }
            }
        },

        {
            "RoleName":
            "CK-Test-CloudFormation-Execution-Role",

            "Description":
            "CloudFormation execution",

            "MaxSessionDuration":
            43200,

            "ManagedPolicies": [
                "arn:aws:iam::aws:policy/PowerUserAccess"
            ],

            "InlinePolicies": {}
        },

        {
            "RoleName":
            "CK-Test-NetworkOne",

            "Description":
            "",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [],

            "InlinePolicies": {}
        },

        {
            "RoleName":
            "CK-Test-AlmaConnect",

            "Description":
            "Alma connect service",

            "MaxSessionDuration":
            3600,

            "ManagedPolicies": [
                "arn:aws:iam::aws:policy/ReadOnlyAccess"
            ],

            "InlinePolicies": {}
        }
    ]

    for role in roles:

        role_name = role[
            "RoleName"
        ]

        try:

            iam.get_role(
                RoleName=role_name
            )

            print(
                f"Already exists: "
                f"{role_name}"
            )

            continue

        except iam.exceptions.NoSuchEntityException:

            pass

        iam.create_role(
            RoleName=role_name,
            Path="/",
            Description=role[
                "Description"
            ],
            MaxSessionDuration=role[
                "MaxSessionDuration"
            ],
            AssumeRolePolicyDocument=
            json.dumps(
                trust_policy
            )
        )

        for policy_arn in role[
            "ManagedPolicies"
        ]:

            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )

        for (
            policy_name,
            policy_document
        ) in role[
            "InlinePolicies"
        ].items():

            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=
                json.dumps(
                    policy_document
                )
            )

        print(
            f"Created: {role_name}"
        )


if __name__ == "__main__":
    main()