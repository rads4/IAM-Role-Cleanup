import json
import os
import threading

from datetime import datetime
from zoneinfo import ZoneInfo


class RoleBackupManager:

    REQUIRED_SCHEMA = {

        "account_id": str,
        "role_name": str,
        "role_arn": str,
        "path": str,
        "description": str,
        "max_session_duration": int,
        "trust_policy": dict,
        "managed_policies": list,
        "inline_policies": dict,
        "instance_profiles": list
    }

    def __init__(
        self,
        backup_dir
    ):

        self.lock = (
            threading.Lock()
        )

        os.makedirs(

            backup_dir,
            exist_ok=True
        )

        timestamp = (

            datetime.now(
                ZoneInfo(
                    "Asia/Kolkata"
                )
            )
            .strftime(
                "%Y-%m-%d_%I-%M-%p_IST"
            )
        )

        self.backup_file = os.path.join(

            backup_dir,

            f"role_backup_{timestamp}.json"
        )

        self.metadata_file = os.path.join(

            backup_dir,

            f"role_backup_{timestamp}.metadata.json"
        )

        self.backup_store = {

            "backup_metadata": {

                "created_at":

                datetime.now(
                    ZoneInfo(
                        "Asia/Kolkata"
                    )
                ).isoformat(),

                "timezone":
                "Asia/Kolkata",

                "version":
                "4.0",

                "accounts": [],

                "total_accounts": 0,

                "total_roles": 0
            },

            "accounts": {}
        }

    def get_backup_file_path(
        self
    ):

        return self.backup_file

    def get_metadata_file_path(
        self
    ):

        return self.metadata_file

    def capture_role_metadata(
        self,
        iam_client,
        account_id,
        role_name,
        role_arn
    ):

        role_response = (
            iam_client.get_role(
                RoleName=
                role_name
            )
        )

        role = role_response[
            "Role"
        ]

        metadata = {

            "account_id":
            account_id,

            "role_name":
            role_name,

            "role_arn":
            role_arn,

            "path":
            role.get(
                "Path",
                "/"
            ),

            "description":
            role.get(
                "Description",
                ""
            ),

            "max_session_duration":
            role.get(
                "MaxSessionDuration",
                3600
            ),

            "trust_policy":
            role[
                "AssumeRolePolicyDocument"
            ],

            "managed_policies":
            [],

            "inline_policies":
            {},

            "instance_profiles":
            []
        }

        paginator = (
            iam_client.get_paginator(
                "list_attached_role_policies"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for policy in page[
                "AttachedPolicies"
            ]:

                metadata[
                    "managed_policies"
                ].append({

                    "PolicyArn":
                    policy[
                        "PolicyArn"
                    ],

                    "PolicyName":
                    policy[
                        "PolicyName"
                    ]
                })

        paginator = (
            iam_client.get_paginator(
                "list_role_policies"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for policy_name in page[
                "PolicyNames"
            ]:

                response = (
                    iam_client.get_role_policy(

                        RoleName=
                        role_name,

                        PolicyName=
                        policy_name
                    )
                )

                metadata[
                    "inline_policies"
                ][
                    policy_name
                ] = response[
                    "PolicyDocument"
                ]

        paginator = (
            iam_client.get_paginator(
                "list_instance_profiles_for_role"
            )
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for profile in page[
                "InstanceProfiles"
            ]:

                metadata[
                    "instance_profiles"
                ].append({

                    "InstanceProfileName":
                    profile[
                        "InstanceProfileName"
                    ]
                })

        self.validate_metadata(

            role_name,
            metadata
        )

        return metadata

    def validate_metadata(
        self,
        role_name,
        metadata
    ):

        missing_keys = []

        for key in self.REQUIRED_SCHEMA:

            if key not in metadata:

                missing_keys.append(
                    key
                )

        if missing_keys:

            raise ValueError(

                f"Role {role_name} "
                f"missing keys: "
                f"{', '.join(missing_keys)}"
            )

        for (
            key,
            expected_type
        ) in self.REQUIRED_SCHEMA.items():

            if not isinstance(

                metadata[key],
                expected_type
            ):

                raise TypeError(

                    f"{role_name} | "
                    f"{key} expected "
                    f"{expected_type.__name__}"
                )

    def persist_role_backup(
        self,
        account_id,
        role_name,
        metadata
    ):

        with self.lock:

            accounts = (
                self.backup_store[
                    "accounts"
                ]
            )

            if account_id not in accounts:

                accounts[
                    account_id
                ] = {

                    "roles": {},

                    "role_count": 0
                }

            accounts[
                account_id
            ][
                "roles"
            ][
                role_name
            ] = metadata

            accounts[
                account_id
            ][
                "role_count"
            ] = len(

                accounts[
                    account_id
                ][
                    "roles"
                ]
            )

            account_list = sorted(
                accounts.keys()
            )

            total_roles = sum(

                account_data[
                    "role_count"
                ]

                for account_data
                in accounts.values()
            )

            self.backup_store[
                "backup_metadata"
            ][
                "accounts"
            ] = account_list

            self.backup_store[
                "backup_metadata"
            ][
                "total_accounts"
            ] = len(
                account_list
            )

            self.backup_store[
                "backup_metadata"
            ][
                "total_roles"
            ] = total_roles

            self._write_backup()

    def _write_backup(
        self
    ):

        temp_file = (
            f"{self.backup_file}.tmp"
        )

        with open(
            temp_file,
            "w"
        ) as file:

            json.dump(

                self.backup_store,

                file,

                indent=2
            )

            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(

            temp_file,

            self.backup_file
        )

    def write_metadata(
        self,
        action,
        dry_run,
        build_number=None,
        build_url=None,
        git_commit=None
    ):

        metadata = {

            "created_at":

            datetime.now(
                ZoneInfo(
                    "Asia/Kolkata"
                )
            ).isoformat(),

            "action":
            action,

            "dry_run":
            dry_run,

            "build_number":
            build_number,

            "build_url":
            build_url,

            "git_commit":
            git_commit,

            "backup_file":
            os.path.basename(
                self.backup_file
            ),

            "accounts":

            self.backup_store[
                "backup_metadata"
            ][
                "accounts"
            ],

            "total_accounts":

            self.backup_store[
                "backup_metadata"
            ][
                "total_accounts"
            ],

            "total_roles":

            self.backup_store[
                "backup_metadata"
            ][
                "total_roles"
            ]
        }

        with open(
            self.metadata_file,
            "w"
        ) as file:

            json.dump(

                metadata,

                file,

                indent=2
            )

    def print_backup_json(
        self,
        logger
    ):

        logger.info(
            "=" * 100
        )

        logger.info(
            "FULL BACKUP JSON"
        )

        logger.info(
            "=" * 100
        )

        with open(
            self.backup_file
        ) as file:

            logger.info(
                file.read()
            )

        logger.info(
            "=" * 100
        )

        logger.info(
            f"BACKUP FILE: "
            f"{self.backup_file}"
        )

        logger.info(
            "=" * 100
        )