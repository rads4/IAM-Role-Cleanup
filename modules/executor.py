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
    get_session
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
    auth_config
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
        role_name,
        iam_client
    ):

        nonlocal completed_roles

        logger.info(
            f"Processing role: "
            f"{role_name}"
        )

        try:

            result = delete_role_fully(
                iam_client=iam_client,
                account_id=account_id,
                role_name=role_name,
                backup_manager=backup_manager,
                error_collector=error_collector,
                dry_run=DRY_RUN
            )

        except Exception:

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
            f"Creating session for "
            f"account {account_id}"
        )

        session = get_session(
            auth_config,
            account_id
        )

        iam_client = session.client(
            "iam"
        )

        with ThreadPoolExecutor(
            max_workers=ROLE_WORKERS
        ) as executor:

            futures = [

                executor.submit(
                    process_role,
                    account_id,
                    role_name,
                    iam_client
                )

                for role_name
                in roles

            ]

            for future in as_completed(
                futures
            ):

                future.result()

    with ThreadPoolExecutor(
        max_workers=ACCOUNT_WORKERS
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