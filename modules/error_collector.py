import csv
import threading

from pathlib import Path

from datetime import (
    datetime
)


class ErrorCollector:

    def __init__(self):

        self.errors = []

        self.lock = (
            threading.Lock()
        )

        self.stats = {

            "BACKUP": {

                "success": 0,
                "failed": 0
            },

            "DELETE": {

                "success": 0,
                "failed": 0
            },

            "RESTORE": {

                "success": 0,
                "failed": 0
            },

            "SKIPPED": 0
        }

    def add(
        self,
        account_id,
        role_name,
        stage,
        operation,
        error_type,
        message,
        role_arn=None
    ):

        with self.lock:

            self.errors.append({

                "timestamp":
                datetime.utcnow().isoformat(),

                "account_id":
                account_id,

                "role_name":
                role_name,

                "role_arn":
                role_arn or "",

                "stage":
                stage,

                "operation":
                operation,

                "error_type":
                error_type,

                "error_message":
                str(message)
            })

    def increment(
        self,
        stage,
        result
    ):

        with self.lock:

            if stage == "SKIPPED":

                self.stats[
                    "SKIPPED"
                ] += 1

                return

            self.stats[
                stage
            ][
                result
            ] += 1

    def count(self):

        return len(
            self.errors
        )

    def get_all(self):

        return self.errors

    def get_stats(self):

        return self.stats

    def write_to_csv(
        self,
        file_name
    ):

        if not self.errors:

            return

        Path(
            file_name
        ).parent.mkdir(

            parents=True,
            exist_ok=True
        )

        with open(
            file_name,
            "w",
            newline=""
        ) as file:

            writer = csv.DictWriter(

                file,

                fieldnames=[

                    "timestamp",
                    "account_id",
                    "role_name",
                    "role_arn",
                    "stage",
                    "operation",
                    "error_type",
                    "error_message"
                ]
            )

            writer.writeheader()

            writer.writerows(
                self.errors
            )

    def write_account_summary(
        self,
        file_name
    ):

        account_summary = {}

        for error in self.errors:

            account_id = error[
                "account_id"
            ]

            account_summary.setdefault(

                account_id,
                0
            )

            account_summary[
                account_id
            ] += 1

        Path(
            file_name
        ).parent.mkdir(

            parents=True,
            exist_ok=True
        )

        with open(
            file_name,
            "w",
            newline=""
        ) as file:

            writer = csv.writer(
                file
            )

            writer.writerow([

                "account_id",
                "error_count"
            ])

            for (
                account_id,
                count
            ) in sorted(
                account_summary.items()
            ):

                writer.writerow([

                    account_id,
                    count
                ])

    def print_summary(
        self,
        logger,
        backup_file=None
    ):

        logger.info(
            "=" * 100
        )

        logger.info(
            "EXECUTION SUMMARY"
        )

        logger.info(
            "=" * 100
        )

        for stage in [

            "BACKUP",
            "DELETE",
            "RESTORE"

        ]:

            logger.info(

                f"{stage:<10} | "
                f"SUCCESS="
                f"{self.stats[stage]['success']} | "
                f"FAILED="
                f"{self.stats[stage]['failed']}"
            )

        logger.info(

            f"SKIPPED    | "
            f"{self.stats['SKIPPED']}"
        )

        if backup_file:

            logger.info(

                f"BACKUP FILE | "
                f"{backup_file}"
            )

        logger.info(

            f"TOTAL ERRORS | "
            f"{self.count()}"
        )

        logger.info(
            "=" * 100
        )

        if self.errors:

            logger.info(
                "ERROR DETAILS"
            )

            logger.info(
                "=" * 100
            )

            for error in self.errors:

                logger.error(

                    f"ACCOUNT_ID="
                    f"{error['account_id']} | "

                    f"ROLE_NAME="
                    f"{error['role_name']} | "

                    f"ROLE_ARN="
                    f"{error['role_arn']} | "

                    f"STAGE="
                    f"{error['stage']} | "

                    f"OPERATION="
                    f"{error['operation']} | "

                    f"ERROR_TYPE="
                    f"{error['error_type']} | "

                    f"MESSAGE="
                    f"{error['error_message']}"
                )