import json

from botocore.exceptions import (
    ClientError
)

from config.settings import (
    CLEANER_ROLE_NAME,
    CLEANER_POLICY_NAME
)


REQUIRED_ACTIONS = sorted([

    "iam:GetRole",
    "iam:ListRolePolicies",
    "iam:GetRolePolicy",
    "iam:ListAttachedRolePolicies",
    "iam:DetachRolePolicy",
    "iam:DeleteRolePolicy",
    "iam:DeleteRole",
    "iam:ListInstanceProfilesForRole",
    "iam:RemoveRoleFromInstanceProfile",
    "iam:CreateRole",
    "iam:AttachRolePolicy",
    "iam:PutRolePolicy",
    "iam:AddRoleToInstanceProfile"

])


def get_cleaner_role_arn(
    account_id
):

    return (
        f"arn:aws:iam::"
        f"{account_id}:role/"
        f"{CLEANER_ROLE_NAME}"
    )


def build_trust_policy(
    trusted_role_arn
):

    return {

        "Version":
        "2012-10-17",

        "Statement": [

            {

                "Effect":
                "Allow",

                "Principal": {

                    "AWS":
                    trusted_role_arn

                },

                "Action":
                "sts:AssumeRole"

            }

        ]

    }


def build_permissions_policy():

    return {

        "Version":
        "2012-10-17",

        "Statement": [

            {

                "Effect":
                "Allow",

                "Action":
                REQUIRED_ACTIONS,

                "Resource":
                "*"

            }

        ]

    }


def cleaner_role_exists(
    iam_client
):

    try:

        iam_client.get_role(
            RoleName=
            CLEANER_ROLE_NAME
        )

        return True

    except ClientError as error:

        if (
            error.response[
                "Error"
            ][
                "Code"
            ]
            ==
            "NoSuchEntity"
        ):

            return False

        raise


def validate_trust_policy(
    iam_client,
    trusted_role_arn,
    logger
):

    role = iam_client.get_role(
        RoleName=
        CLEANER_ROLE_NAME
    )

    current_policy = (
        role[
            "Role"
        ][
            "AssumeRolePolicyDocument"
        ]
    )

    expected_policy = (
        build_trust_policy(
            trusted_role_arn
        )
    )

    if current_policy == expected_policy:

        logger.info(
            "Cleaner trust policy validated"
        )

        return False

    logger.warning(
        "Cleaner trust policy drift detected. Repairing..."
    )

    iam_client.update_assume_role_policy(

        RoleName=
        CLEANER_ROLE_NAME,

        PolicyDocument=
        json.dumps(
            expected_policy
        )
    )

    logger.info(
        "Cleaner trust policy updated"
    )

    return True


def validate_permissions_policy(
    iam_client,
    logger
):

    expected_policy = (
        build_permissions_policy()
    )

    try:

        current_policy = (
            iam_client.get_role_policy(

                RoleName=
                CLEANER_ROLE_NAME,

                PolicyName=
                CLEANER_POLICY_NAME
            )[
                "PolicyDocument"
            ]
        )

        current_actions = sorted(

            current_policy[
                "Statement"
            ][0][
                "Action"
            ]
        )

        if current_actions == REQUIRED_ACTIONS:

            logger.info(
                "Cleaner permissions validated"
            )

            return False

    except ClientError:

        pass

    logger.warning(
        "Cleaner permissions drift detected. Repairing..."
    )

    iam_client.put_role_policy(

        RoleName=
        CLEANER_ROLE_NAME,

        PolicyName=
        CLEANER_POLICY_NAME,

        PolicyDocument=
        json.dumps(
            expected_policy
        )
    )

    logger.info(
        "Cleaner permissions updated"
    )

    return True


def create_cleaner_role(
    iam_client,
    trusted_role_arn,
    logger
):

    trust_policy = (
        build_trust_policy(
            trusted_role_arn
        )
    )

    permissions_policy = (
        build_permissions_policy()
    )

    iam_client.create_role(

        RoleName=
        CLEANER_ROLE_NAME,

        AssumeRolePolicyDocument=
        json.dumps(
            trust_policy
        )
    )

    iam_client.put_role_policy(

        RoleName=
        CLEANER_ROLE_NAME,

        PolicyName=
        CLEANER_POLICY_NAME,

        PolicyDocument=
        json.dumps(
            permissions_policy
        )
    )

    logger.info(
        f"Created role: "
        f"{CLEANER_ROLE_NAME}"
    )

    return True


def ensure_cleaner_role(
    iam_client,
    trusted_role_arn,
    logger
):

    if not cleaner_role_exists(
        iam_client
    ):

        return create_cleaner_role(

            iam_client=
            iam_client,

            trusted_role_arn=
            trusted_role_arn,

            logger=
            logger
        )

    logger.info(
        f"{CLEANER_ROLE_NAME} "
        f"already exists"
    )

    trust_updated = (
        validate_trust_policy(

            iam_client=
            iam_client,

            trusted_role_arn=
            trusted_role_arn,

            logger=
            logger
        )
    )

    permissions_updated = (
        validate_permissions_policy(

            iam_client=
            iam_client,

            logger=
            logger
        )
    )

    return (
        trust_updated
        or
        permissions_updated
    )