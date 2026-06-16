import json
import sys

from pathlib import Path

from botocore.exceptions import (
    ClientError
)

from modules.logger import (
    get_logger
)

from modules.auth import (
    get_operator_session,
    get_cleaner_session
)

from modules.iam_setup import (
    get_cleaner_role_arn
)


def role_exists(
    iam_client,
    role_name
):

    try:

        iam_client.get_role(
            RoleName=role_name
        )

        return True

    except ClientError as error:

        if (
            error.response[
                "Error"
            ][
                "Code"
            ]
            ==
            "NoSuchEntity"
        ):

            return False

        raise


def restore_role(
    iam_client,
    role_name,
    metadata,
    restore_profiles,
    dry_run,
    logger
):

    if role_exists(
        iam_client,
        role_name
    ):

        logger.warning(
            f"Role already exists: "
            f"{role_name}"
        )

        return "skipped"

    if dry_run:

        logger.info(
            f"DRY RUN -> "
            f"{role_name}"
        )

        return "dry_run"

    iam_client.create_role(

        RoleName=
        role_name,

        Path=
        metadata["path"],

        Description=
        metadata[
            "description"
        ],

        MaxSessionDuration=
        metadata[
            "max_session_duration"
        ],

        AssumeRolePolicyDocument=
        json.dumps(
            metadata[
                "trust_policy"
            ]
        )
    )

    for policy in metadata[
        "managed_policies"
    ]:

        iam_client.attach_role_policy(

            RoleName=
            role_name,

            PolicyArn=
            policy[
                "PolicyArn"
            ]
        )

    for (
        policy_name,
        policy_document
    ) in metadata[
        "inline_policies"
    ].items():

        iam_client.put_role_policy(

            RoleName=
            role_name,

            PolicyName=
            policy_name,

            PolicyDocument=
            json.dumps(
                policy_document
            )
        )

    if restore_profiles:

        for profile in metadata[
            "instance_profiles"
        ]:

            try:

                iam_client.add_role_to_instance_profile(

                    InstanceProfileName=
                    profile[
                        "InstanceProfileName"
                    ],

                    RoleName=
                    role_name
                )

            except Exception:

                pass

    logger.info(
        f"Restored role: "
        f"{role_name}"
    )

    return "restored"


def select_backup_file():

    backup_dir = Path(
        "backups"
    )

    backup_files = sorted(
        backup_dir.glob(
            "*.json"
        ),
        reverse=True
    )

    if not backup_files:

        raise Exception(
            "No backup files found"
        )

    print(
        "\nAvailable Backup Files:\n"
    )

    for index, file in enumerate(
        backup_files,
        start=1
    ):

        print(
            f"{index}. "
            f"{file.name}"
        )

    while True:

        choice = input(
            "\nSelect Backup: "
        ).strip()

        try:

            return str(
                backup_files[
                    int(choice) - 1
                ]
            )

        except Exception:

            print(
                "Invalid selection"
            )


def ask_yes_no(
    question
):

    while True:

        answer = input(
            f"\n{question} "
            f"(y/n): "
        ).strip().lower()

        if answer in [
            "y",
            "yes"
        ]:

            return True

        if answer in [
            "n",
            "no"
        ]:

            return False


def main():

    logger = get_logger()

    backup_file = (
        select_backup_file()
    )

    with open(
        backup_file
    ) as file:

        backup_data = json.load(
            file
        )

    cross_account_role = input(
        "\nCross Account Role Name: "
    ).strip()

    restore_profiles = (
        ask_yes_no(
            "Restore Instance Profiles?"
        )
    )

    dry_run = (
        ask_yes_no(
            "Dry Run?"
        )
    )

    operator_session = (
        get_operator_session()
    )

    restored = 0
    skipped = 0
    failed = 0

    for (
        account_id,
        account_data
    ) in backup_data[
        "accounts"
    ].items():

        try:

            cleaner_session = (
                get_cleaner_session(

                    operator_session=
                    operator_session,

                    account_id=
                    account_id,

                    cross_account_role=
                    cross_account_role,

                    cleaner_role_arn=
                    get_cleaner_role_arn(
                        account_id
                    )
                )
            )

            iam_client = (
                cleaner_session.client(
                    "iam"
                )
            )

        except Exception as error:

            logger.error(
                f"{account_id} | "
                f"SESSION | "
                f"{str(error)}"
            )

            failed += 1

            continue

        roles = (
            account_data[
                "roles"
            ]
        )

        for (
            role_name,
            metadata
        ) in roles.items():

            try:

                result = restore_role(

                    iam_client=
                    iam_client,

                    role_name=
                    role_name,

                    metadata=
                    metadata,

                    restore_profiles=
                    restore_profiles,

                    dry_run=
                    dry_run,

                    logger=
                    logger
                )

                if result == "restored":

                    restored += 1

                else:

                    skipped += 1

            except Exception as error:

                failed += 1

                logger.error(
                    f"{account_id} | "
                    f"{role_name} | "
                    f"{str(error)}"
                )

    logger.info(
        "=" * 60
    )

    logger.info(
        f"Restored: "
        f"{restored}"
    )

    logger.info(
        f"Skipped: "
        f"{skipped}"
    )

    logger.info(
        f"Failed: "
        f"{failed}"
    )

    logger.info(
        "=" * 60
    )

    if failed:

        sys.exit(1)


if __name__ == "__main__":

    main()