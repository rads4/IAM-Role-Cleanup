import json
import sys
import argparse

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
            error.response["Error"]["Code"]
            ==
            "NoSuchEntity"
        ):

            return False

        raise


def validate_role_identity(
    account_id,
    role_name,
    role_arn
):

    expected_prefix = (
        f"arn:aws:iam::{account_id}:role/"
    )

    if not role_arn.startswith(
        expected_prefix
    ):

        raise ValueError(

            f"RoleArn does not belong "
            f"to account {account_id}: "
            f"{role_arn}"
        )

    arn_role_name = (
        role_arn.split("/")[-1]
    )

    if arn_role_name != role_name:

        raise ValueError(

            f"RoleName mismatch. "
            f"Backup={role_name}, "
            f"ARN={arn_role_name}"
        )


def restore_role(
    iam_client,
    metadata,
    restore_profiles,
    dry_run,
    logger
):

    account_id = metadata[
        "account_id"
    ]

    role_name = metadata[
        "role_name"
    ]

    role_arn = metadata[
        "role_arn"
    ]

    validate_role_identity(

        account_id=
        account_id,

        role_name=
        role_name,

        role_arn=
        role_arn
    )

    if role_exists(
        iam_client,
        role_name
    ):

        logger.warning(
            f"{account_id} | "
            f"{role_name} | "
            f"Already exists"
        )

        return "skipped"

    if dry_run:

        logger.info(
            f"{account_id} | "
            f"{role_name} | "
            f"DRY RUN"
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

            except Exception as error:

                logger.warning(

                    f"{account_id} | "
                    f"{role_name} | "
                    f"Profile restore failed | "
                    f"{str(error)}"
                )

    logger.info(

        f"{account_id} | "
        f"{role_name} | "
        f"Restored"
    )

    return "restored"


def load_backup(
    backup_file
):

    with open(
        backup_file
    ) as file:

        return json.load(
            file
        )


def get_roles_to_restore(
    backup_data,
    restore_scope,
    account_id=None,
    role_names=None
):

    results = {}

    accounts = (
        backup_data[
            "accounts"
        ]
    )

    if restore_scope == "FULL":

        return accounts

    if restore_scope == "ACCOUNT":

        if not account_id:

            raise ValueError(
                "--account-id required "
                "for ACCOUNT restore"
            )

        if account_id not in accounts:

            raise ValueError(

                f"Account not found: "
                f"{account_id}"
            )

        results[
            account_id
        ] = accounts[
            account_id
        ]

        return results

    if restore_scope == "ROLE":

        if not account_id:

            raise ValueError(
                "--account-id required "
                "for ROLE restore"
            )

        if not role_names:

            raise ValueError(
                "--role-names required "
                "for ROLE restore"
            )

        if account_id not in accounts:

            raise ValueError(

                f"Account not found: "
                f"{account_id}"
            )

        requested_roles = {

            role.strip()

            for role
            in role_names.split(",")

            if role.strip()
        }

        selected_roles = {}

        for (
            role_name,
            metadata
        ) in accounts[
            account_id
        ][
            "roles"
        ].items():

            if role_name in requested_roles:

                selected_roles[
                    role_name
                ] = metadata

        if not selected_roles:

            raise ValueError(
                "No matching roles found "
                "in backup file"
            )

        results[
            account_id
        ] = {

            "roles":
            selected_roles
        }

        return results

    raise ValueError(
        f"Invalid restore scope: "
        f"{restore_scope}"
    )


def parse_args():

    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--backup-file",
        required=True
    )

    parser.add_argument(
        "--restore-scope",
        choices=[
            "FULL",
            "ACCOUNT",
            "ROLE"
        ],
        required=True
    )

    parser.add_argument(
        "--account-id"
    )

    parser.add_argument(
        "--role-names"
    )

    parser.add_argument(
        "--restore-profiles",
        default="true"
    )

    parser.add_argument(
        "--dry-run",
        default="true"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    logger = get_logger()

    backup_data = load_backup(
        args.backup_file
    )

    restore_profiles = (

        args.restore_profiles.lower()
        ==
        "true"
    )

    dry_run = (

        args.dry_run.lower()
        ==
        "true"
    )

    restore_targets = (
        get_roles_to_restore(

            backup_data=
            backup_data,

            restore_scope=
            args.restore_scope,

            account_id=
            args.account_id,

            role_names=
            args.role_names
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
    ) in restore_targets.items():

        try:

            cleaner_session = (
                get_cleaner_session(

                    operator_session=
                    operator_session,

                    cleaner_role_arn=
                    get_cleaner_role_arn(
                        account_id
                    ),

                    account_id=
                    account_id
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

        for metadata in (

            account_data[
                "roles"
            ].values()

        ):

            try:

                result = restore_role(

                    iam_client=
                    iam_client,

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
                    f"{metadata.get('role_name')} | "
                    f"{str(error)}"
                )

    logger.info(
        "=" * 100
    )

    logger.info(
        f"RESTORED : "
        f"{restored}"
    )

    logger.info(
        f"SKIPPED  : "
        f"{skipped}"
    )

    logger.info(
        f"FAILED   : "
        f"{failed}"
    )

    logger.info(
        "=" * 100
    )

    if failed:

        sys.exit(1)


if __name__ == "__main__":

    main()