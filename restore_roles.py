import argparse
import json
import sys

from botocore.exceptions import ClientError

from modules.auth import (
    get_account_session
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

        managed_policy_count = len(
            metadata[
                "managed_policies"
            ]
        )

        inline_policy_count = len(
            metadata[
                "inline_policies"
            ]
        )

        instance_profile_count = len(
            metadata[
                "instance_profiles"
            ]
        )

        logger.info(
            "=" * 60
        )

        logger.info(
            f"DRY RUN: {role_name}"
        )

        logger.info(
            f"Path: "
            f"{metadata['path']}"
        )

        logger.info(
            f"Description: "
            f"{metadata['description']}"
        )

        logger.info(
            f"MaxSessionDuration: "
            f"{metadata['max_session_duration']}"
        )

        logger.info(
            f"Managed Policies: "
            f"{managed_policy_count}"
        )

        logger.info(
            f"Inline Policies: "
            f"{inline_policy_count}"
        )

        logger.info(
            f"Instance Profiles: "
            f"{instance_profile_count}"
        )

        logger.info(
            "Would create role"
        )

        logger.info(
            "Would attach managed policies"
        )

        logger.info(
            "Would recreate inline policies"
        )

        if restore_profiles:

            logger.info(
                "Would restore instance profile associations"
            )

        logger.info(
            "=" * 60
        )

        return "dry_run"

    create_role_kwargs = {
        "RoleName":
        role_name,

        "Path":
        metadata["path"],

        "Description":
        metadata["description"],

        "MaxSessionDuration":
        metadata[
            "max_session_duration"
        ],

        "AssumeRolePolicyDocument":
        json.dumps(
            metadata[
                "trust_policy"
            ]
        )
    }

    iam_client.create_role(
        **create_role_kwargs
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

            iam_client.add_role_to_instance_profile(
                InstanceProfileName=
                profile[
                    "InstanceProfileName"
                ],
                RoleName=role_name
            )

    logger.info(
        f"Restored role: "
        f"{role_name}"
    )

    return "restored"


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

    session = get_account_session()

    iam_client = session.client(
        "iam"
    )

    with open(
        args.backup_file
    ) as file:

        backup_data = json.load(
            file
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

    for (
        role_name,
        metadata
    ) in backup_data.items():

        if (
            selected_roles
            and role_name
            not in selected_roles
        ):

            continue

        try:

            result = restore_role(
                iam_client=iam_client,
                role_name=role_name,
                metadata=metadata,
                restore_profiles=args.restore_profiles,
                dry_run=args.dry_run,
                logger=logger
            )

            if result == "restored":

                restored += 1

            else:

                skipped += 1

        except Exception as e:

            failed += 1

            logger.error(
                f"{role_name}: {str(e)}"
            )

    logger.info(
        "=" * 60
    )

    logger.info(
        f"Restored: {restored}"
    )

    logger.info(
        f"Skipped: {skipped}"
    )

    logger.info(
        f"Failed: {failed}"
    )

    logger.info(
        "=" * 60
    )

    if failed:

        sys.exit(1)


if __name__ == "__main__":
    main()