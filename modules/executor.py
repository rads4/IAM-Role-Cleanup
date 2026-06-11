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
    total_roles
):

    global completed_roles

    try:

        logger.info(
            f"Processing role: {role_name}"
        )

        delete_role_fully(
            iam_client,
            account_id,
            role_name,
            DRY_RUN
        )

        with progress_lock:

            completed_roles += 1

            logger.info(
                f"Progress: "
                f"{completed_roles}/"
                f"{total_roles}"
            )

        logger.info(
            f"Completed role: {role_name}"
        )

    except Exception as e:

        error_collector.add(
            account_id,
            role_name,
            type(e).__name__,
            str(e)
        )

        logger.error(
            f"Failed role: {role_name}"
        )


def process_account(
    account_id,
    roles,
    logger,
    error_collector,
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
    logger
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