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
    get_account_session
)

from modules.iam_cleaner import (
    delete_role_fully
)

from modules.error_collector import (
    ErrorCollector
)


progress_lock = Lock()

completed_roles = 0


def process_role(
    iam_client,
    account_id,
    role_name,
    logger,
    error_collector,
    backup_manager,
    total_roles
):

    global completed_roles

    try:

        logger.info(
            f"Processing role: "
            f"{role_name}"
        )

        result = delete_role_fully(
            iam_client=iam_client,
            account_id=account_id,
            role_name=role_name,
            backup_manager=backup_manager,
            error_collector=error_collector,
            dry_run=DRY_RUN
        )

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

    except Exception as e:

        logger.error(
            f"Failed role: "
            f"{role_name} "
            f"({str(e)})"
        )


def process_account(
    account_id,
    roles,
    logger,
    error_collector,
    backup_manager,
    total_roles
):

    session = get_account_session()

    iam_client = session.client(
        "iam"
    )

    with ThreadPoolExecutor(
        max_workers=ROLE_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                process_role,
                iam_client,
                account_id,
                role,
                logger,
                error_collector,
                backup_manager,
                total_roles
            )

            for role in roles
        ]

        for future in as_completed(
            futures
        ):

            future.result()


def execute(
    grouped_roles,
    logger,
    backup_manager
):

    error_collector = (
        ErrorCollector()
    )

    total_roles = sum(
        len(roles)
        for roles
        in grouped_roles.values()
    )

    with ThreadPoolExecutor(
        max_workers=ACCOUNT_WORKERS
    ) as executor:

        futures = [

            executor.submit(
                process_account,
                account_id,
                roles,
                logger,
                error_collector,
                backup_manager,
                total_roles
            )

            for account_id,
            roles
            in grouped_roles.items()
        ]

        for future in as_completed(
            futures
        ):

            try:

                future.result()

            except Exception as e:

                logger.error(
                    str(e)
                )

    return error_collector