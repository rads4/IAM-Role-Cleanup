from modules.csv_reader import load_roles
from modules.executor import execute
from modules.logger import get_logger
from modules.auth import get_account_session

from config.settings import (
    INPUT_CSV
)


def main():

    logger = get_logger()

    grouped_roles = load_roles(
        INPUT_CSV
    )

    session = get_account_session()

    caller = session.client(
        "sts"
    ).get_caller_identity()

    logger.info(
        f"Executing as: "
        f"{caller['Arn']}"
    )

    logger.info(
        f"Account: "
        f"{caller['Account']}"
    )

    csv_accounts = list(
        grouped_roles.keys()
    )

    logger.info(
        f"CSV Account(s): "
        f"{csv_accounts}"
    )

    if (
        len(csv_accounts) != 1
        or csv_accounts[0] != caller["Account"]
    ):

        raise Exception(
            "CSV account does not match "
            "logged-in account"
        )

    total_roles = sum(
        len(v)
        for v
        in grouped_roles.values()
    )

    logger.info(
        f"Accounts found: "
        f"{len(grouped_roles)}"
    )

    logger.info(
        f"Total roles: "
        f"{total_roles}"
    )

    sample_roles = []

    for roles in grouped_roles.values():
        sample_roles.extend(
            roles[:5]
        )

    logger.info(
        f"Sample roles: "
        f"{sample_roles}"
    )

    error_collector = execute(
        grouped_roles,
        logger
    )

    if error_collector.count():

        error_collector.write_to_csv(
            "output/role_deletion_errors.csv"
        )

        logger.info(
            f"Errors captured: "
            f"{error_collector.count()}"
        )

    else:

        logger.info(
            "Execution completed successfully"
        )


if __name__ == "__main__":
    main()