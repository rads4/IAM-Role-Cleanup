from pathlib import Path
import csv

from modules.csv_reader import load_roles

from modules.executor import execute

from modules.logger import get_logger

from modules.auth import (
    build_auth_config
)

from modules.role_backup import (
    RoleBackupManager
)

from modules.profile_manager import (
    create_profile,
    profile_exists
)

from config.settings import (
    BACKUP_DIR
)


def select_file(
    directory,
    pattern,
    title
):

    path = Path(
        directory
    )

    if not path.exists():

        raise Exception(
            f"{directory} not found"
        )

    files = sorted(
        path.glob(pattern)
    )

    if not files:

        raise Exception(
            f"No {title} found"
        )

    print(
        f"\nAvailable {title}:\n"
    )

    for index, file in enumerate(
        files,
        start=1
    ):

        print(
            f"{index}. {file.name}"
        )

    while True:

        choice = input(
            "\nSelect: "
        ).strip()

        try:

            return str(
                files[
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


def load_credentials(
    credentials_file
):

    account_profiles = {}

    with open(
        credentials_file
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            account_id = (
                row[
                    "AccountId"
                ].strip()
            )

            permission = (
                row[
                    "Permission"
                ].strip()
            )

            profile_name = (
                f"{account_id}-"
                f"{permission}"
            )

            if not profile_exists(
                profile_name
            ):

                create_profile(
                    profile_name=
                    profile_name,

                    access_key=
                    row[
                        "AccessKeyId"
                    ].strip(),

                    secret_key=
                    row[
                        "SecretAccessKey"
                    ].strip(),

                    region=
                    row[
                        "Region"
                    ].strip()
                )

            account_profiles[
                account_id
            ] = profile_name

    return account_profiles


def validate_accounts(
    grouped_roles,
    account_profiles
):

    missing_accounts = []

    for account_id in grouped_roles:

        if (
            account_id
            not in account_profiles
        ):

            missing_accounts.append(
                account_id
            )

    if missing_accounts:

        raise Exception(
            "Missing credentials for "
            f"accounts: "
            f"{missing_accounts}"
        )


def main():

    logger = get_logger()

    roles_csv = select_file(
        "dummy-inputs",
        "*roles*.csv",
        "Role CSV Files"
    )

    credentials_csv = select_file(
        "dummy-inputs",
        "account_credentials.csv",
        "Credential Files"
    )

    grouped_roles = load_roles(
        roles_csv
    )

    account_profiles = (
        load_credentials(
            credentials_csv
        )
    )

    validate_accounts(
        grouped_roles,
        account_profiles
    )

    auth_config = (
        build_auth_config(
            account_profiles
        )
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

    logger.info(
        f"Profiles loaded: "
        f"{len(account_profiles)}"
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