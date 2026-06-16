import csv
import json

import boto3


ROLE_NAMES = [

    "CK-Jenkins-Test-App-01",
    "CK-Jenkins-Test-App-02",
    "CK-Jenkins-Test-App-03",
    "CK-Jenkins-Test-App-04",
    "CK-Jenkins-Test-App-05"

]


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


def build_role_definition(
    role_name
):

    return {

        "RoleName":
        role_name,

        "Description":
        f"Jenkins POC role {role_name}",

        "MaxSessionDuration":
        3600,

        "ManagedPolicies": [

            "arn:aws:iam::aws:policy/ReadOnlyAccess"

        ],

        "InlinePolicies": {

            f"{role_name}-InlinePolicy": {

                "Version":
                "2012-10-17",

                "Statement": [

                    {

                        "Effect":
                        "Allow",

                        "Action": [

                            "s3:ListBucket"

                        ],

                        "Resource":
                        "*"

                    }

                ]

            }

        }

    }


def main():

    profile_name = (
        select_profile()
    )

    session = boto3.Session(
        profile_name=profile_name
    )

    sts = session.client(
        "sts"
    )

    account_id = (
        sts.get_caller_identity()[
            "Account"
        ]
    )

    iam = session.client(
        "iam"
    )

    trust_policy = {

        "Version":
        "2012-10-17",

        "Statement": [

            {

                "Effect":
                "Allow",

                "Principal": {

                    "Service":
                    "ec2.amazonaws.com"

                },

                "Action":
                "sts:AssumeRole"

            }

        ]

    }

    csv_rows = []

    for role_name in ROLE_NAMES:

        role = build_role_definition(
            role_name
        )

        try:

            existing_role = (
                iam.get_role(
                    RoleName=role_name
                )
            )

            role_arn = (
                existing_role[
                    "Role"
                ][
                    "Arn"
                ]
            )

            print(
                f"Already exists: "
                f"{role_name}"
            )

        except iam.exceptions.NoSuchEntityException:

            iam.create_role(

                RoleName=
                role_name,

                Path="/",

                Description=
                role[
                    "Description"
                ],

                MaxSessionDuration=
                role[
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

                    RoleName=
                    role_name,

                    PolicyArn=
                    policy_arn
                )

            for (
                policy_name,
                policy_document
            ) in role[
                "InlinePolicies"
            ].items():

                iam.put_role_policy(

                    RoleName=
                    role_name,

                    PolicyName=
                    policy_name,

                    PolicyDocument=
                    json.dumps(
                        policy_document
                    )
                )

            role_arn = (
                f"arn:aws:iam::"
                f"{account_id}:role/"
                f"{role_name}"
            )

            print(
                f"Created: "
                f"{role_name}"
            )

        csv_rows.append({

            "AccountId":
            account_id,

            "Arn":
            role_arn,

            "Name":
            role_name

        })

    output_file = (
        "output/"
        "jenkins_poc_roles.csv"
    )

    with open(
        output_file,
        "w",
        newline=""
    ) as file:

        writer = csv.DictWriter(

            file,

            fieldnames=[

                "AccountId",
                "Arn",
                "Name"

            ]
        )

        writer.writeheader()

        writer.writerows(
            csv_rows
        )

    print(
        f"\nGenerated CSV: "
        f"{output_file}"
    )


if __name__ == "__main__":

    main()