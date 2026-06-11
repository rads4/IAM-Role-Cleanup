import csv
from collections import defaultdict


def load_roles(csv_path):
    grouped_roles = defaultdict(list)

    with open(csv_path, newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            account_id = row["AccountId"].strip()
            role_name = row["Name"].strip()

            grouped_roles[account_id].append(
                role_name
            )

    return grouped_roles