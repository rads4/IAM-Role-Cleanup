import boto3


def get_operator_session():

    return boto3.Session()


def assume_role(
    session,
    role_arn,
    session_name
):

    sts = session.client(
        "sts"
    )

    response = sts.assume_role(

        RoleArn=
        role_arn,

        RoleSessionName=
        session_name
    )

    credentials = response[
        "Credentials"
    ]

    return boto3.Session(

        aws_access_key_id=
        credentials[
            "AccessKeyId"
        ],

        aws_secret_access_key=
        credentials[
            "SecretAccessKey"
        ],

        aws_session_token=
        credentials[
            "SessionToken"
        ]
    )


def get_account_id(
    session
):

    sts = session.client(
        "sts"
    )

    return sts.get_caller_identity()[
        "Account"
    ]


def validate_session_account(
    session,
    expected_account_id
):

    actual_account_id = (
        get_account_id(
            session
        )
    )

    if (
        actual_account_id
        != expected_account_id
    ):

        raise Exception(

            f"Expected account "
            f"{expected_account_id} "
            f"but connected to "
            f"{actual_account_id}"
        )


def get_cleaner_session(
    operator_session,
    cleaner_role_arn,
    account_id
):

    cleaner_session = (
        assume_role(

            session=
            operator_session,

            role_arn=
            cleaner_role_arn,

            session_name=
            f"cleanup-"
            f"{account_id}"
        )
    )

    validate_session_account(

        cleaner_session,
        account_id
    )

    return cleaner_session