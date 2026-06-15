import json
import sys
from pathlib import Path

from botocore.exceptions import (
    ClientError
)

from modules.auth import (
    build_auth_config,
    get_session
)

from modules.logger import (
    get_logger
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

    except ClientError as e:

        if (
            e.response["Error"]["Code"]
            == "NoSuchEntity"
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
        RoleName=role_name,
        Path=metadata["path"],
        Description=metadata[
            "description"
        ],
        MaxSessionDuration=metadata[
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
            RoleName=role_name,
            PolicyArn=policy[
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
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(
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
                    RoleName=role_name
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

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection"
            )


def select_restore_mode():

    print(
        "\nRestore Mode\n"
    )

    print(
        "1. All Accounts -> All Roles"
    )

    print(
        "2. All Accounts -> Selected Roles"
    )

    print(
        "3. Selected Account -> All Roles"
    )

    print(
        "4. Selected Account -> Selected Roles"
    )

    while True:

        choice = input(
            "\nSelect: "
        ).strip()

        if choice in [
            "1",
            "2",
            "3",
            "4"
        ]:

            return choice

        print(
            "Invalid selection"
        )


def select_accounts(
    backup_data,
    mode
):

    accounts = sorted(
        backup_data[
            "accounts"
        ].keys()
    )

    if mode in [
        "1",
        "2"
    ]:

        return accounts

    print(
        "\nAvailable Accounts:\n"
    )

    for index, account_id in enumerate(
        accounts,
        start=1
    ):

        print(
            f"{index}. "
            f"{account_id}"
        )

    while True:

        choice = input(
            "\nSelect Account: "
        ).strip()

        try:

            return [
                accounts[
                    int(choice) - 1
                ]
            ]

        except (
            ValueError,
            IndexError
        ):

            print(
                "Invalid selection"
            )


def select_roles(
    backup_data,
    selected_accounts,
    mode
):

    if mode in [
        "1",
        "3"
    ]:

        return None

    all_roles = set()

    for account_id in selected_accounts:

        roles = (
            backup_data[
                "accounts"
            ][
                account_id
            ][
                "roles"
            ]
        )

        all_roles.update(
            roles.keys()
        )

    all_roles = sorted(
        all_roles
    )

    print(
        "\nAvailable Roles:\n"
    )

    for index, role in enumerate(
        all_roles,
        start=1
    ):

        print(
            f"{index}. "
            f"{role}"
        )

    choice = input(
        "\nEnter role numbers "
        "(comma separated): "
    ).strip()

    selected = set()

    for item in choice.split(
        ","
    ):

        selected.add(
            all_roles[
                int(item.strip()) - 1
            ]
        )

    return selected


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

    mode = (
        select_restore_mode()
    )

    selected_accounts = (
        select_accounts(
            backup_data,
            mode
        )
    )

    selected_roles = (
        select_roles(
            backup_data,
            selected_accounts,
            mode
        )
    )

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

    account_profiles = {}

    for account_id in selected_accounts:

        account_profiles[
            account_id
        ] = (
            f"{account_id}-admin"
        )

    auth_config = (
        build_auth_config(
            account_profiles
        )
    )

    restored = 0
    skipped = 0
    failed = 0

    for account_id in selected_accounts:

        session = get_session(
            auth_config,
            account_id
        )

        iam_client = session.client(
            "iam"
        )

        roles = (
            backup_data[
                "accounts"
            ][
                account_id
            ][
                "roles"
            ]
        )

        for (
            role_name,
            metadata
        ) in roles.items():

            if (
                selected_roles
                and role_name
                not in selected_roles
            ):

                continue

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

            except Exception as e:

                failed += 1

                logger.error(
                    f"{account_id} | "
                    f"{role_name} | "
                    f"{str(e)}"
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