from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from threading import Lock

from config.settings import (
    ACCOUNT_WORKERS,
    ROLE_WORKERS,
)

from modules.auth import (
    assume_role,
    validate_session_account
)

from modules.iam_setup import (
    get_cleaner_role_arn,
    validate_cleaner_role
)

from modules.error_collector import (
    ErrorCollector
)

from modules.iam_cleaner import (
    delete_role_fully
)

from modules.logger import (
    print_account_header,
    print_role_header
)


def execute(
    grouped_roles,
    logger,
    backup_manager,
    operator_session,
    dry_run
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

        role_arn = role[
            "role_arn"
        ]

        print_role_header(

            logger=
            logger,

            account_id=
            account_id,

            role_name=
            role_name,

            role_arn=
            role_arn
        )

        try:

            result = delete_role_fully(

                iam_client=
                iam_client,

                account_id=
                account_id,

                role_name=
                role_name,

                role_arn=
                role_arn,

                backup_manager=
                backup_manager,

                error_collector=
                error_collector,

                dry_run=
                dry_run,

                logger=
                logger
            )

        except Exception as error:

            logger.error(

                f"ACCOUNT_ID={account_id} | "
                f"ROLE_NAME={role_name} | "
                f"ROLE_ARN={role_arn} | "
                f"ERROR={str(error)}"
            )

            result = "failed"

        with progress_lock:

            completed_roles += 1

            logger.info(

                f"PROGRESS : "
                f"{completed_roles}/"
                f"{total_roles}"
            )

        logger.info(

            f"ROLE RESULT | "
            f"{account_id} | "
            f"{role_name} | "
            f"{result}"
        )

    def process_account(
        account_id,
        roles
    ):

        print_account_header(
            logger,
            account_id
        )

        cleaner_role_arn = (
            get_cleaner_role_arn(
                account_id
            )
        )

        try:

            logger.info(

                f"ASSUMING CLEANER ROLE : "
                f"{cleaner_role_arn}"
            )

            cleaner_session = (

                assume_role(

                    session=
                    operator_session,

                    role_arn=
                    cleaner_role_arn,

                    session_name=
                    f"cleanup-{account_id}"
                )
            )

            validate_session_account(

                cleaner_session,
                account_id
            )

            logger.info(
                "SESSION VALIDATED"
            )

        except Exception as error:

            logger.error(

                f"{account_id} | "
                f"ACCOUNT_INIT | "
                f"{str(error)}"
            )

            error_collector.add(

                account_id=
                account_id,

                role_name=
                "ACCOUNT_INIT",

                role_arn=
                cleaner_role_arn,

                stage=
                "DELETE",

                operation=
                "ASSUME_CLEANER_ROLE",

                error_type=
                type(error).__name__,

                message=
                str(error)
            )

            return

        iam_client = (
            cleaner_session.client(
                "iam"
            )
        )

        try:

            validation_result = (

                validate_cleaner_role(
                    iam_client,
                    logger
                )
            )

            if not validation_result:

                logger.error(

                    f"{account_id} | "
                    f"CLEANER ROLE VALIDATION FAILED"
                )

                error_collector.add(

                    account_id=
                    account_id,

                    role_name=
                    "ACCOUNT_INIT",

                    role_arn=
                    cleaner_role_arn,

                    stage=
                    "DELETE",

                    operation=
                    "VALIDATE_CLEANER_ROLE",

                    error_type=
                    "CleanerRoleValidationFailed",

                    message=
                    "Cleaner role validation failed"
                )

                return

        except Exception as error:

            logger.error(

                f"{account_id} | "
                f"CLEANER VALIDATION ERROR | "
                f"{str(error)}"
            )

            error_collector.add(

                account_id=
                account_id,

                role_name=
                "ACCOUNT_INIT",

                role_arn=
                cleaner_role_arn,

                stage=
                "DELETE",

                operation=
                "VALIDATE_CLEANER_ROLE",

                error_type=
                type(error).__name__,

                message=
                str(error)
            )

            return

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

            for (
                account_id,
                roles
            )
            in grouped_roles.items()

        ]

        for future in as_completed(
            futures
        ):

            future.result()

    return error_collector