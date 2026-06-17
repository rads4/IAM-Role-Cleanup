import time

from botocore.exceptions import ClientError

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
        role_arn.split(
            "/"
        )[-1]
    )

    if arn_role_name != role_name:

        raise ValueError(

            f"RoleName mismatch. "
            f"CSV Name={role_name}, "
            f"ARN Name={arn_role_name}"
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


def _execute_deletion(
    iam_client,
    role_name,
    dry_run=False
):

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

            if not dry_run:

                _retryable_call(

                    iam_client.detach_role_policy,

                    RoleName=
                    role_name,

                    PolicyArn=
                    policy[
                        "PolicyArn"
                    ]
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

            if not dry_run:

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

            if not dry_run:

                _retryable_call(

                    iam_client.remove_role_from_instance_profile,

                    InstanceProfileName=
                    profile[
                        "InstanceProfileName"
                    ],

                    RoleName=
                    role_name
                )

    if not dry_run:

        _retryable_call(

            iam_client.delete_role,

            RoleName=
            role_name
        )


def delete_role_fully(
    iam_client,
    account_id,
    role_name,
    role_arn,
    backup_manager,
    error_collector,
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

            account_id,
            role_name,
            "BACKUP",
            "CAPTURE_ROLE_METADATA",
            type(error).__name__,
            str(error)
        )

        return "backup_failed"

    try:

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

            account_id,
            role_name,
            "BACKUP",
            "PERSIST_ROLE_BACKUP",
            type(error).__name__,
            str(error)
        )

        return "backup_failed"

    for attempt in range(
        1,
        MAX_RETRY_ATTEMPTS + 1
    ):

        try:

            _execute_deletion(

                iam_client=
                iam_client,

                role_name=
                role_name,

                dry_run=
                dry_run
            )

            error_collector.increment(
                "DELETE",
                "success"
            )

            return "success"

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
                ==
                "NoSuchEntity"
            ):

                error_collector.increment(
                    "DELETE",
                    "failed"
                )

                error_collector.add(

                    account_id,
                    role_name,
                    "DELETE",
                    "DELETE_ROLE",
                    code,
                    str(error)
                )

                raise

            if (
                code
                not in
                RETRYABLE_CODES
            ):

                error_collector.increment(
                    "DELETE",
                    "failed"
                )

                error_collector.add(

                    account_id,
                    role_name,
                    "DELETE",
                    "DELETE_ROLE",
                    code,
                    str(error)
                )

                raise

            if (
                attempt
                ==
                MAX_RETRY_ATTEMPTS
            ):

                error_collector.increment(
                    "DELETE",
                    "failed"
                )

                error_collector.add(

                    account_id,
                    role_name,
                    "DELETE",
                    "DELETE_ROLE",
                    code,
                    str(error)
                )

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

        except Exception as error:

            error_collector.increment(
                "DELETE",
                "failed"
            )

            error_collector.add(

                account_id,
                role_name,
                "DELETE",
                "DELETE_ROLE",
                type(error).__name__,
                str(error)
            )

            raise