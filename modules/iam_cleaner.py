import time

from botocore.exceptions import (
    ClientError
)

from config.settings import (
    MAX_RETRY_ATTEMPTS,
    BASE_BACKOFF_SECONDS
)


RETRYABLE_CODES = {

    "Throttling",
    "ThrottlingException",
    "RequestLimitExceeded",
    "TooManyRequestsException",
    "DeleteConflict",
    "ConcurrentModification",
    "ServiceFailure"
}


def validate_role_identity(
    account_id,
    role_name,
    role_arn
):

    expected_prefix = (
        f"arn:aws:iam::{account_id}:role/"
    )

    if not role_arn.startswith(
        expected_prefix
    ):

        raise ValueError(

            f"RoleArn does not belong "
            f"to account {account_id}: "
            f"{role_arn}"
        )

    arn_role_name = (
        role_arn.split("/")[-1]
    )

    if arn_role_name != role_name:

        raise ValueError(

            f"RoleName mismatch. "
            f"CSV={role_name}, "
            f"ARN={arn_role_name}"
        )


def _retryable_call(
    func,
    **kwargs
):

    for attempt in range(
        1,
        MAX_RETRY_ATTEMPTS + 1
    ):

        try:

            return func(
                **kwargs
            )

        except ClientError as error:

            code = (
                error.response[
                    "Error"
                ][
                    "Code"
                ]
            )

            if (
                code
                not in
                RETRYABLE_CODES
            ):

                raise

            if (
                attempt
                ==
                MAX_RETRY_ATTEMPTS
            ):

                raise

            delay = (
                BASE_BACKOFF_SECONDS *
                (
                    2 **
                    (
                        attempt - 1
                    )
                )
            )

            time.sleep(
                delay
            )


def delete_role_fully(
    iam_client,
    account_id,
    role_name,
    role_arn,
    backup_manager,
    error_collector,
    logger,
    dry_run=False
):

    validate_role_identity(

        account_id=
        account_id,

        role_name=
        role_name,

        role_arn=
        role_arn
    )

    logger.info(
        f"BACKUP START | "
        f"{role_name}"
    )

    try:

        metadata = (

            backup_manager
            .capture_role_metadata(

                iam_client=
                iam_client,

                account_id=
                account_id,

                role_name=
                role_name,

                role_arn=
                role_arn
            )
        )

        backup_manager.persist_role_backup(

            account_id=
            account_id,

            role_name=
            role_name,

            metadata=
            metadata
        )

        error_collector.increment(
            "BACKUP",
            "success"
        )

        logger.info(
            f"BACKUP SUCCESS | "
            f"{role_name}"
        )

    except Exception as error:

        error_collector.increment(
            "BACKUP",
            "failed"
        )

        error_collector.increment(
            "SKIPPED",
            None
        )

        error_collector.add(

            account_id=
            account_id,

            role_name=
            role_name,

            role_arn=
            role_arn,

            stage=
            "BACKUP",

            operation=
            "CAPTURE_ROLE_METADATA",

            error_type=
            type(error).__name__,

            message=
            str(error)
        )

        logger.error(

            f"BACKUP FAILED | "
            f"{role_name} | "
            f"{str(error)}"
        )

        return "backup_failed"

    if dry_run:

        logger.info(

            f"DRY RUN | "
            f"DELETE SKIPPED | "
            f"{role_name}"
        )

        error_collector.increment(
            "DELETE",
            "success"
        )

        return "dry_run"

    try:

        logger.info(
            f"DELETE START | "
            f"{role_name}"
        )

        paginator = (
            iam_client.get_paginator(
                "list_attached_role_policies"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for policy in page[
                "AttachedPolicies"
            ]:

                logger.info(

                    f"DETACH POLICY | "
                    f"{policy['PolicyArn']}"
                )

                _retryable_call(

                    iam_client.detach_role_policy,

                    RoleName=
                    role_name,

                    PolicyArn=
                    policy["PolicyArn"]
                )

        paginator = (
            iam_client.get_paginator(
                "list_role_policies"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for policy_name in page[
                "PolicyNames"
            ]:

                logger.info(

                    f"DELETE INLINE POLICY | "
                    f"{policy_name}"
                )

                _retryable_call(

                    iam_client.delete_role_policy,

                    RoleName=
                    role_name,

                    PolicyName=
                    policy_name
                )

        paginator = (
            iam_client.get_paginator(
                "list_instance_profiles_for_role"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for profile in page[
                "InstanceProfiles"
            ]:

                logger.info(

                    f"REMOVE PROFILE | "
                    f"{profile['InstanceProfileName']}"
                )

                _retryable_call(

                    iam_client.remove_role_from_instance_profile,

                    InstanceProfileName=
                    profile[
                        "InstanceProfileName"
                    ],

                    RoleName=
                    role_name
                )

        logger.info(
            f"DELETE ROLE | "
            f"{role_name}"
        )

        _retryable_call(

            iam_client.delete_role,

            RoleName=
            role_name
        )

        error_collector.increment(
            "DELETE",
            "success"
        )

        logger.info(
            f"DELETE SUCCESS | "
            f"{role_name}"
        )

        return "success"

    except Exception as error:

        error_collector.increment(
            "DELETE",
            "failed"
        )

        error_collector.add(

            account_id=
            account_id,

            role_name=
            role_name,

            role_arn=
            role_arn,

            stage=
            "DELETE",

            operation=
            "DELETE_ROLE",

            error_type=
            type(error).__name__,

            message=
            str(error)
        )

        logger.error(

            f"DELETE FAILED | "
            f"{role_name} | "
            f"{str(error)}"
        )

        raise