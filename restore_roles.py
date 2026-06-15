import argparse
import json
import sys

from modules.auth import (
    build_auth_config,
    get_session
)

from modules.logger import (
    get_logger
)

from botocore.exceptions import (
    ClientError
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


def select_accounts(
    backup_data
):

    accounts = sorted(
        backup_data[
            "accounts"
        ].keys()
    )

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

    print(
        "\n0. Restore All"
    )

    choice = input(
        "\nSelect: "
    ).strip()

    if choice == "0":

        return accounts

    return [
        accounts[
            int(choice) - 1
        ]
    ]


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "backup_file"
    )

    parser.add_argument(
        "--roles"
    )

    parser.add_argument(
        "--restore-profiles",
        action="store_true"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true"
    )

    args = parser.parse_args()

    logger = get_logger()

    with open(
        args.backup_file
    ) as file:

        backup_data = json.load(
            file
        )

    selected_accounts = (
        select_accounts(
            backup_data
        )
    )

    account_profiles = {}

    for account_id in selected_accounts:

        permission = input(
            f"\nPermission "
            f"suffix for "
            f"{account_id} "
            f"(admin): "
        ).strip()

        if not permission:

            permission = "admin"

        account_profiles[
            account_id
        ] = (
            f"{account_id}-"
            f"{permission}"
        )

    auth_config = (
        build_auth_config(
            account_profiles
        )
    )

    selected_roles = None

    if args.roles:

        selected_roles = set(

            role.strip()

            for role in args.roles.split(
                ","
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
                    args.restore_profiles,

                    dry_run=
                    args.dry_run,

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