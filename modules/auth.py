import boto3


LOCAL_PROFILE = "LOCAL_PROFILE"

ASSUME_ROLE = "ASSUME_ROLE"


def get_available_profiles():

    session = boto3.Session()

    return sorted(
        session.available_profiles
    )


def build_local_auth_config(
    account_profiles
):

    return {
        "mode": LOCAL_PROFILE,
        "account_profiles":
        account_profiles
    }


def build_assume_role_auth_config(
    account_roles,
    base_profile
):

    return {
        "mode": ASSUME_ROLE,
        "base_profile":
        base_profile,
        "account_roles":
        account_roles
    }


def get_session(
    auth_config,
    account_id
):

    mode = auth_config[
        "mode"
    ]

    if mode == LOCAL_PROFILE:

        profile_name = (
            auth_config[
                "account_profiles"
            ][account_id]
        )

        return boto3.Session(
            profile_name=profile_name
        )

    if mode == ASSUME_ROLE:

        role_arn = (
            auth_config[
                "account_roles"
            ][account_id]
        )

        base_session = boto3.Session(
            profile_name=
            auth_config[
                "base_profile"
            ]
        )

        sts = base_session.client(
            "sts"
        )

        response = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=
            "IAMRoleCleanup"
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

    raise ValueError(
        f"Unsupported mode: "
        f"{mode}"
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