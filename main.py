from pathlib import Path

from modules.csv_reader import (
    load_roles
)

from modules.executor import (
    execute
)

from modules.logger import (
    get_logger
)

from modules.auth import (
    get_operator_session
)

from modules.role_backup import (
    RoleBackupManager
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


def main():

    logger = get_logger()

    roles_csv = select_file(

        "inputs",
        "*.csv",
        "Role CSV Files"
    )

    grouped_roles = load_roles(
        roles_csv
    )

    operator_session = (
        get_operator_session()
    )

    total_roles = sum(

        len(roles)

        for roles
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

        grouped_roles=
        grouped_roles,

        logger=
        logger,

        backup_manager=
        backup_manager,

        operator_session=
        operator_session
    )

    if error_collector.count():

        Path(
            "output"
        ).mkdir(
            exist_ok=True
        )

        error_collector.write_to_csv(
            "output/role_deletion_errors.csv"
        )

        logger.warning(
            "Error report generated: "
            "output/role_deletion_errors.csv"
        )

    error_collector.print_summary(

        logger,
        backup_manager.get_backup_file_path()
    )


if __name__ == "__main__":

    main()