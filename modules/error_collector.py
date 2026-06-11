import csv
import threading
from datetime import datetime


class ErrorCollector:

    def __init__(self):

        self.errors = []

        self.lock = threading.Lock()

    def add(
        self,
        account_id,
        role_name,
        error_type,
        message
    ):

        with self.lock:

            self.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "account_id": account_id,
                "role_name": role_name,
                "error_type": error_type,
                "error_message": message
            })

    def count(self):

        return len(self.errors)

    def get_all(self):

        return self.errors

    def write_to_csv(self, file_name):

        if not self.errors:
            return

        with open(
            file_name,
            "w",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=self.errors[0].keys()
            )

            writer.writeheader()

            writer.writerows(
                self.errors
            )