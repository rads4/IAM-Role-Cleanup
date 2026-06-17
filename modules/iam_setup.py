from botocore.exceptions import (
    ClientError
)

from config.settings import (
    CLEANER_ROLE_NAME,
    CLEANER_POLICY_NAME,
    TRUSTED_PRINCIPAL_ARN
)


REQUIRED_ACTIONS = sorted([

    # Backup

    "iam:GetRole",
    "iam:GetRolePolicy",
    "iam:ListRolePolicies",
    "iam:ListAttachedRolePolicies",
    "iam:ListInstanceProfilesForRole",
    "iam:GetInstanceProfile",

    # Delete

    "iam:DetachRolePolicy",
    "iam:DeleteRolePolicy",
    "iam:RemoveRoleFromInstanceProfile",
    "iam:DeleteRole",

    # Restore

    "iam:CreateRole",
    "iam:AttachRolePolicy",
    "iam:PutRolePolicy",
    "iam:AddRoleToInstanceProfile"
])


def get_cleaner_role_arn(
    account_id
):

    return (
        f"arn:aws:iam::{account_id}:role/"
        f"{CLEANER_ROLE_NAME}"
    )


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


def validate_permissions_policy(
    iam_client
):

    try:

        policy = (
            iam_client.get_role_policy(

                RoleName=
                CLEANER_ROLE_NAME,

                PolicyName=
                CLEANER_POLICY_NAME
            )
        )

        policy_document = (
            policy[
                "PolicyDocument"
            ]
        )

        discovered_actions = []

        for statement in (
            policy_document[
                "Statement"
            ]
        ):

            actions = (
                statement.get(
                    "Action",
                    []
                )
            )

            if isinstance(
                actions,
                str
            ):

                discovered_actions.append(
                    actions
                )

            else:

                discovered_actions.extend(
                    actions
                )

        current_actions = sorted(
            set(
                discovered_actions
            )
        )

        return (
            current_actions
            ==
            REQUIRED_ACTIONS
        )

    except ClientError:

        return False


def validate_trust_policy(
    iam_client,
    logger
):

    try:

        role = iam_client.get_role(

            RoleName=
            CLEANER_ROLE_NAME
        )

        trust_policy = (

            role[
                "Role"
            ][
                "AssumeRolePolicyDocument"
            ]
        )

        statements = (
            trust_policy.get(
                "Statement",
                []
            )
        )

        if not statements:

            logger.warning(
                "Cleaner role trust policy empty"
            )

            return False

        trusted_principal = (
            statements[0]
            .get(
                "Principal",
                {}
            )
            .get(
                "AWS"
            )
        )

        if (
            trusted_principal
            !=
            TRUSTED_PRINCIPAL_ARN
        ):

            logger.warning(
                "Cleaner trust policy drift detected"
            )

            logger.warning(
                f"Expected: "
                f"{TRUSTED_PRINCIPAL_ARN}"
            )

            logger.warning(
                f"Found: "
                f"{trusted_principal}"
            )

            return False

        logger.info(
            "Cleaner trust policy validated"
        )

        return True

    except Exception as error:

        logger.warning(
            f"Trust policy validation failed: "
            f"{str(error)}"
        )

        return False


def validate_cleaner_role(
    iam_client,
    logger
):

    if not cleaner_role_exists(
        iam_client
    ):

        logger.error(
            f"{CLEANER_ROLE_NAME} "
            f"does not exist"
        )

        return False

    logger.info(
        f"{CLEANER_ROLE_NAME} "
        f"exists"
    )

    trust_valid = (
        validate_trust_policy(
            iam_client,
            logger
        )
    )

    permissions_valid = (
        validate_permissions_policy(
            iam_client
        )
    )

    if permissions_valid:

        logger.info(
            "Cleaner permissions validated"
        )

    else:

        logger.warning(
            "Cleaner permissions drift detected"
        )

    return (
        trust_valid
        and
        permissions_valid
    )