import time

from botocore.exceptions import ClientError

from config.settings import (
    MAX_RETRY_ATTEMPTS,
    BASE_BACKOFF_SECONDS
)


def _retryable_call(func, **kwargs):

    for attempt in range(
        1,
        MAX_RETRY_ATTEMPTS + 1
    ):

        try:

            return func(**kwargs)

        except ClientError as e:

            code = e.response[
                "Error"
            ]["Code"]

            if (
                "Throttl" not in code
                and "Rate" not in code
            ):
                raise

            if attempt == MAX_RETRY_ATTEMPTS:
                raise

            delay = (
                BASE_BACKOFF_SECONDS *
                (2 ** (attempt - 1))
            )

            time.sleep(delay)


def _execute_deletion(
    iam_client,
    role_name,
    dry_run=False
):

    paginator = iam_client.get_paginator(
        "list_attached_role_policies"
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
                    RoleName=role_name,
                    PolicyArn=policy[
                        "PolicyArn"
                    ]
                )

    paginator = iam_client.get_paginator(
        "list_role_policies"
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
                    RoleName=role_name,
                    PolicyName=policy_name
                )

    paginator = iam_client.get_paginator(
        "list_instance_profiles_for_role"
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
                    RoleName=role_name
                )

    if not dry_run:

        _retryable_call(
            iam_client.delete_role,
            RoleName=role_name
        )


def delete_role_fully(
    iam_client,
    account_id,
    role_name,
    backup_manager,
    error_collector,
    dry_run=False
):

    #
    # BACKUP CAPTURE
    #

    try:

        metadata = (
            backup_manager
            .capture_role_metadata(
                iam_client,
                role_name
            )
        )

    except Exception as e:

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
            type(e).__name__,
            str(e)
        )

        return "backup_failed"

    #
    # BACKUP PERSIST
    #

    try:

        backup_manager.persist_role_backup(
            account_id,
            role_name,
            metadata
        )

        error_collector.increment(
            "BACKUP",
            "success"
        )

    except Exception as e:

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
            type(e).__name__,
            str(e)
        )

        return "backup_failed"

    #
    # DELETE
    #

    for attempt in range(
        1,
        MAX_RETRY_ATTEMPTS + 1
    ):

        try:

            _execute_deletion(
                iam_client,
                role_name,
                dry_run
            )

            error_collector.increment(
                "DELETE",
                "success"
            )

            return "success"

        except ClientError as e:

            code = e.response[
                "Error"
            ]["Code"]

            if code == "NoSuchEntity":

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
                    str(e)
                )

                raise

            if (
                "Throttl" not in code
                and "Rate" not in code
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
                    str(e)
                )

                raise

            if attempt == MAX_RETRY_ATTEMPTS:

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
                    str(e)
                )

                raise

            delay = (
                BASE_BACKOFF_SECONDS *
                (2 ** (attempt - 1))
            )

            time.sleep(delay)

        except Exception as e:

            error_collector.increment(
                "DELETE",
                "failed"
            )

            error_collector.add(
                account_id,
                role_name,
                "DELETE",
                "DELETE_ROLE",
                type(e).__name__,
                str(e)
            )

            raise