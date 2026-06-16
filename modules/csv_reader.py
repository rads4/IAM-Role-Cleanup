import csv

from collections import defaultdict


def load_roles(
    csv_path
):

    grouped_roles = defaultdict(
        list
    )

    with open(
        csv_path,
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            account_id = (
                row[
                    "AccountId"
                ].strip()
            )

            if "Arn" in row:

                role_arn = (
                    row[
                        "Arn"
                    ].strip()
                )

                role_name = (
                    row[
                        "Name"
                    ].strip()
                )

            else:

                role_arn = (
                    row[
                        "RoleArn"
                    ].strip()
                )

                role_name = (
                    role_arn
                    .split("/")[-1]
                )

            grouped_roles[
                account_id
            ].append({

                "role_arn":
                role_arn,

                "role_name":
                role_name

            })

    return grouped_roles