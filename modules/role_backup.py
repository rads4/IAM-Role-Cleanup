import json
import os
import threading

from datetime import datetime
from zoneinfo import ZoneInfo


class RoleBackupManager:

    REQUIRED_SCHEMA = {
        "path": str,
        "description": str,
        "max_session_duration": int,
        "trust_policy": dict,
        "managed_policies": list,
        "inline_policies": dict,
        "instance_profiles": list
    }

    def __init__(self, backup_dir):

        self.lock = threading.Lock()

        os.makedirs(
            backup_dir,
            exist_ok=True
        )

        timestamp = (
            datetime.now(
                ZoneInfo("Asia/Kolkata")
            )
            .strftime(
                "%Y-%m-%d_%I-%M-%p_IST"
            )
        )

        self.backup_file = os.path.join(
            backup_dir,
            f"role_backup_{timestamp}.json"
        )

        self.backup_store = {
            "backup_metadata": {
                "created_at": (
                    datetime.now(
                        ZoneInfo("Asia/Kolkata")
                    ).isoformat()
                ),
                "accounts": [],
                "total_accounts": 0,
                "total_roles": 0
            },
            "accounts": {}
        }

    def get_backup_file_path(self):

        return self.backup_file

    def capture_role_metadata(
        self,
        iam_client,
        role_name
    ):

        role_response = iam_client.get_role(
            RoleName=role_name
        )

        role = role_response["Role"]

        metadata = {
            "path": role.get(
                "Path",
                "/"
            ),
            "description": role.get(
                "Description",
                ""
            ),
            "max_session_duration": role.get(
                "MaxSessionDuration",
                3600
            ),
            "trust_policy": role.get(
                "AssumeRolePolicyDocument"
            ),
            "managed_policies": [],
            "inline_policies": {},
            "instance_profiles": []
        }

        paginator = iam_client.get_paginator(
            "list_attached_role_policies"
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
                    "PolicyArn": policy[
                        "PolicyArn"
                    ],
                    "PolicyName": policy[
                        "PolicyName"
                    ]
                })

        paginator = iam_client.get_paginator(
            "list_role_policies"
        )

        for page in paginator.paginate(
            RoleName=role_name
        ):

            for policy_name in page[
                "PolicyNames"
            ]:

                policy_response = (
                    iam_client.get_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                )

                metadata[
                    "inline_policies"
                ][policy_name] = (
                    policy_response[
                        "PolicyDocument"
                    ]
                )

        paginator = iam_client.get_paginator(
            "list_instance_profiles_for_role"
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
                f"Role {role_name} missing "
                f"required backup keys: "
                f"{', '.join(missing_keys)}"
            )

        for (
            key,
            expected_type
        ) in self.REQUIRED_SCHEMA.items():

            value = metadata[key]

            if not isinstance(
                value,
                expected_type
            ):

                raise TypeError(
                    f"Role {role_name}: "
                    f"'{key}' must be "
                    f"{expected_type.__name__}, "
                    f"found "
                    f"{type(value).__name__}"
                )

        if metadata[
            "trust_policy"
        ] is None:

            raise ValueError(
                f"Role {role_name}: "
                f"trust_policy cannot be None"
            )

    def persist_role_backup(
        self,
        account_id,
        role_name,
        metadata
    ):

        with self.lock:

            accounts = self.backup_store[
                "accounts"
            ]

            if account_id not in accounts:

                accounts[
                    account_id
                ] = {
                    "roles": {}
                }

            accounts[
                account_id
            ][
                "roles"
            ][
                role_name
            ] = metadata

            account_list = sorted(
                accounts.keys()
            )

            total_roles = sum(
                len(
                    account_data[
                        "roles"
                    ]
                )
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