import boto3


def get_available_profiles():

    session = boto3.Session()

    return sorted(
        session.available_profiles
    )


def build_auth_config(
    account_profiles
):

    return {
        "account_profiles":
        account_profiles
    }


def get_session(
    auth_config,
    account_id
):

    profile_name = (
        auth_config[
            "account_profiles"
        ][account_id]
    )

    return boto3.Session(
        profile_name=profile_name
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