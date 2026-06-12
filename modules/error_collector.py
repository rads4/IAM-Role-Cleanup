import csv
import threading

from datetime import datetime


class ErrorCollector:

    def __init__(self):

        self.errors = []

        self.lock = threading.Lock()

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
        message
    ):

        with self.lock:

            self.errors.append({

                "timestamp":
                datetime.utcnow().isoformat(),

                "account_id":
                account_id,

                "role_name":
                role_name,

                "stage":
                stage,

                "operation":
                operation,

                "error_type":
                error_type,

                "error_message":
                message
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

            if (
                stage
                not in self.stats
            ):

                raise ValueError(
                    f"Unknown stage: {stage}"
                )

            if (
                result
                not in self.stats[
                    stage
                ]
            ):

                raise ValueError(
                    f"Unknown result: {result}"
                )

            self.stats[
                stage
            ][
                result
            ] += 1

    def get_stats(self):

        return self.stats

    def count(self):

        return len(
            self.errors
        )

    def get_all(self):

        return self.errors

    def write_to_csv(
        self,
        file_name
    ):

        if not self.errors:
            return

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

    def print_summary(
        self,
        logger,
        backup_file=None
    ):

        logger.info(
            "=" * 60
        )

        logger.info(
            "Execution Summary"
        )

        logger.info(
            "=" * 60
        )

        for stage in [

            "BACKUP",
            "DELETE",
            "RESTORE"

        ]:

            logger.info(
                f"{stage:<12} "
                f"Success="
                f"{self.stats[stage]['success']} "
                f"Failed="
                f"{self.stats[stage]['failed']}"
            )

        logger.info(
            f"SKIPPED     "
            f"{self.stats['SKIPPED']}"
        )

        if backup_file:

            logger.info(
                f"Backup File: "
                f"{backup_file}"
            )

        logger.info(
            f"Total Errors: "
            f"{self.count()}"
        )

        logger.info(
            "=" * 60
        )