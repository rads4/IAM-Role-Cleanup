import time

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from threading import Lock

from config.settings import (
    ACCOUNT_WORKERS,
    ROLE_WORKERS,
    DRY_RUN
)

from modules.auth import (
    assume_role,
    validate_session_account
)

from modules.iam_setup import (
    ensure_cleaner_role,
    get_cleaner_role_arn
)

from modules.error_collector import (
    ErrorCollector
)

from modules.iam_cleaner import (
    delete_role_fully
)


def execute(
    grouped_roles,
    logger,
    backup_manager,
    operator_session,
    cross_account_role
):

    error_collector = ErrorCollector()

    progress_lock = Lock()

    total_roles = sum(
        len(roles)
        for roles
        in grouped_roles.values()
    )

    completed_roles = 0

    def process_role(
        account_id,
        role,
        iam_client
    ):

        nonlocal completed_roles

        role_name = role[
            "role_name"
        ]

        logger.info(
            f"Processing role: "
            f"{role_name}"
        )

        try:

            result = delete_role_fully(

                iam_client=
                iam_client,

                account_id=
                account_id,

                role_name=
                role_name,

                backup_manager=
                backup_manager,

                error_collector=
                error_collector,

                dry_run=
                DRY_RUN
            )

        except Exception as error:

            logger.error(
                f"{account_id} | "
                f"{role_name} | "
                f"{str(error)}"
            )

            result = "failed"

        with progress_lock:

            completed_roles += 1

            logger.info(
                f"Progress: "
                f"{completed_roles}/"
                f"{total_roles}"
            )

        logger.info(
            f"Completed role: "
            f"{role_name} "
            f"({result})"
        )

    def process_account(
        account_id,
        roles
    ):

        logger.info(
            f"Processing account "
            f"{account_id}"
        )

        cross_account_role_arn = (

            f"arn:aws:iam::"
            f"{account_id}:role/"
            f"{cross_account_role}"

        )

        logger.info(
            f"Assuming bootstrap role: "
            f"{cross_account_role_arn}"
        )

        bootstrap_session = (
            assume_role(

                session=
                operator_session,

                role_arn=
                cross_account_role_arn,

                session_name=
                f"bootstrap-"
                f"{account_id}"
            )
        )

        validate_session_account(
            bootstrap_session,
            account_id
        )

        bootstrap_iam = (
            bootstrap_session.client(
                "iam"
            )
        )

        cleaner_updated = (
            ensure_cleaner_role(

                iam_client=
                bootstrap_iam,

                trusted_role_arn=
                cross_account_role_arn,

                logger=
                logger
            )
        )

        if cleaner_updated:

            logger.info(
                "Waiting for IAM policy propagation..."
            )

            time.sleep(15)

        cleaner_role_arn = (
            get_cleaner_role_arn(
                account_id
            )
        )

        logger.info(
            f"Assuming cleaner role: "
            f"{cleaner_role_arn}"
        )

        cleaner_session = (
            assume_role(

                session=
                bootstrap_session,

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

        iam_client = (
            cleaner_session.client(
                "iam"
            )
        )

        with ThreadPoolExecutor(
            max_workers=
            ROLE_WORKERS
        ) as executor:

            futures = [

                executor.submit(
                    process_role,
                    account_id,
                    role,
                    iam_client
                )

                for role
                in roles

            ]

            for future in as_completed(
                futures
            ):

                future.result()

    with ThreadPoolExecutor(
        max_workers=
        ACCOUNT_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                process_account,
                account_id,
                roles
            )

            for account_id,
            roles
            in grouped_roles.items()

        ]

        for future in as_completed(
            futures
        ):

            future.result()

    return error_collector