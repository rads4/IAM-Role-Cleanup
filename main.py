import os
import argparse

from pathlib import Path

from modules.csv_reader import (
    load_roles
)

from modules.executor import (
    execute
)

from modules.logger import (
    get_logger,
    print_banner
)

from modules.auth import (
    get_operator_session
)

from modules.role_backup import (
    RoleBackupManager
)

from modules.slack_notifier import (
    SlackNotifier
)

from config.settings import (
    BACKUP_DIR,
    SLACK_ENABLED
)


def parse_args():

    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--csv-file",
        required=True
    )

    parser.add_argument(
        "--dry-run",
        default="true"
    )

    parser.add_argument(
        "--build-number",
        default=""
    )

    parser.add_argument(
        "--build-url",
        default=""
    )

    parser.add_argument(
        "--git-commit",
        default=""
    )

    return parser.parse_args()


def main():

    args = parse_args()

    logger = get_logger()

    dry_run = (
        args.dry_run.lower()
        == "true"
    )

    print_banner(
        logger,
        "IAM ROLE CLEANER"
    )

    logger.info(
        f"ACTION       : DELETE"
    )

    logger.info(
        f"DRY_RUN      : {dry_run}"
    )

    logger.info(
        f"CSV_FILE     : "
        f"{args.csv_file}"
    )

    grouped_roles = (
        load_roles(
            args.csv_file
        )
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
        f"ACCOUNTS     : "
        f"{len(grouped_roles)}"
    )

    logger.info(
        f"TOTAL ROLES  : "
        f"{total_roles}"
    )

    backup_manager = (
        RoleBackupManager(
            BACKUP_DIR
        )
    )

    logger.info(
        f"BACKUP FILE  : "
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
        operator_session,

        dry_run=
        dry_run
    )

    backup_manager.write_metadata(

        action=
        "DELETE",

        dry_run=
        dry_run,

        build_number=
        args.build_number,

        build_url=
        args.build_url,

        git_commit=
        args.git_commit
    )

    backup_manager.print_backup_json(
        logger
    )

    error_csv = None
    account_summary_csv = None

    if error_collector.count():

        Path(
            "output"
        ).mkdir(
            exist_ok=True
        )

        error_csv = (
            "output/role_deletion_errors.csv"
        )

        account_summary_csv = (
            "output/account_error_summary.csv"
        )

        error_collector.write_to_csv(
            error_csv
        )

        error_collector.write_account_summary(
            account_summary_csv
        )

        logger.warning(
            "Error report generated:"
        )

        logger.warning(
            error_csv
        )

    error_collector.print_summary(

        logger,

        backup_manager.get_backup_file_path()
    )

    if SLACK_ENABLED:

        try:

            slack_token = os.environ[
                "SLACK_BOT_TOKEN"
            ]

            slack_channel = os.environ[
                "SLACK_CHANNEL_ID"
            ]

            slack = (
                SlackNotifier(

                    token=
                    slack_token,

                    channel_id=
                    slack_channel,

                    logger=
                    logger
                )
            )

            slack.send_summary(

                action=
                "DELETE",

                dry_run=
                dry_run,

                accounts=
                len(grouped_roles),

                roles=
                total_roles,

                build_number=
                args.build_number,

                build_url=
                args.build_url
            )

            slack.upload_backup_bundle(

                backup_file=
                backup_manager.get_backup_file_path(),

                metadata_file=
                backup_manager.get_metadata_file_path(),

                error_csv=
                error_csv,

                account_summary_csv=
                account_summary_csv
            )

        except Exception as error:

            logger.error(

                f"Slack upload failed: "
                f"{str(error)}"
            )


if __name__ == "__main__":

    main()