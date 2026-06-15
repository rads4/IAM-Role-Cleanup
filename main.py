from pathlib import Path

from modules.csv_reader import load_roles

from modules.executor import execute

from modules.logger import get_logger

from modules.auth import (
    get_available_profiles,
    build_local_auth_config,
    build_assume_role_auth_config
)

from modules.role_backup import (
    RoleBackupManager
)

from config.settings import (
    BACKUP_DIR
)


def select_csv():

    csv_files = []

    for directory in [
        "inputs",
        "dummy-inputs"
    ]:

        path = Path(directory)

        if path.exists():

            csv_files.extend(
                sorted(
                    path.glob(
                        "*.csv"
                    )
                )
            )

    if not csv_files:

        raise Exception(
            "No CSV files found"
        )

    print(
        "\nAvailable CSV Files:\n"
    )

    for index, file in enumerate(
        csv_files,
        start=1
    ):

        print(
            f"{index}. {file}"
        )

    while True:

        choice = input(
            "\nSelect CSV: "
        ).strip()

        try:

            return str(
                csv_files[
                    int(choice) - 1
                ]
            )

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection"
            )


def select_execution_mode():

    print(
        "\nExecution Mode\n"
    )

    print(
        "1. Local Profile"
    )

    print(
        "2. Assume Role"
    )

    while True:

        choice = input(
            "\nSelect Mode: "
        ).strip()

        if choice == "1":

            return "LOCAL"

        if choice == "2":

            return "ASSUME_ROLE"

        print(
            "Invalid selection"
        )


def select_profile():

    profiles = (
        get_available_profiles()
    )

    if not profiles:

        raise Exception(
            "No AWS profiles found"
        )

    print(
        "\nAvailable AWS Profiles:\n"
    )

    for index, profile in enumerate(
        profiles,
        start=1
    ):

        print(
            f"{index}. {profile}"
        )

    while True:

        choice = input(
            "\nSelect Profile: "
        ).strip()

        try:

            return profiles[
                int(choice) - 1
            ]

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection"
            )


def build_local_mapping(
    accounts
):

    account_profiles = {}

    for account_id in sorted(
        accounts
    ):

        print(
            f"\nAccount: "
            f"{account_id}"
        )

        profile = (
            select_profile()
        )

        account_profiles[
            account_id
        ] = profile

    return (
        build_local_auth_config(
            account_profiles
        )
    )


def build_assume_role_mapping(
    accounts
):

    print(
        "\nBase Profile "
        "(Operator Account)"
    )

    base_profile = (
        select_profile()
    )

    account_roles = {}

    for account_id in sorted(
        accounts
    ):

        role_arn = input(
            f"\nRole ARN for "
            f"{account_id}: "
        ).strip()

        account_roles[
            account_id
        ] = role_arn

    return (
        build_assume_role_auth_config(
            account_roles,
            base_profile
        )
    )


def main():

    logger = get_logger()

    selected_csv = (
        select_csv()
    )

    grouped_roles = load_roles(
        selected_csv
    )

    accounts = list(
        grouped_roles.keys()
    )

    logger.info(
        f"CSV Selected: "
        f"{selected_csv}"
    )

    logger.info(
        f"Accounts Found: "
        f"{accounts}"
    )

    mode = (
        select_execution_mode()
    )

    if mode == "LOCAL":

        auth_config = (
            build_local_mapping(
                accounts
            )
        )

    else:

        auth_config = (
            build_assume_role_mapping(
                accounts
            )
        )

    total_roles = sum(
        len(v)
        for v
        in grouped_roles.values()
    )

    logger.info(
        f"Accounts found: "
        f"{len(accounts)}"
    )

    logger.info(
        f"Total roles: "
        f"{total_roles}"
    )

    backup_manager = (
        RoleBackupManager(
            BACKUP_DIR
        )
    )

    logger.info(
        f"Backup file initialized: "
        f"{backup_manager.get_backup_file_path()}"
    )

    error_collector = execute(
        grouped_roles=grouped_roles,
        logger=logger,
        backup_manager=backup_manager,
        auth_config=auth_config
    )

    if error_collector.count():

        error_collector.write_to_csv(
            "output/role_deletion_errors.csv"
        )

    error_collector.print_summary(
        logger,
        backup_manager.get_backup_file_path()
    )


if __name__ == "__main__":
    main()