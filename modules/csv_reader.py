import csv

from collections import defaultdict


def load_roles(
    csv_path
):

    grouped_roles = defaultdict(
        list
    )

    seen_roles = set()

    with open(
        csv_path,
        newline=""
    ) as file:

        reader = csv.DictReader(
            file
        )

        required_columns = {

            "AccountId",
            "Arn",
            "Name"
        }

        missing_columns = (
            required_columns
            -
            set(
                reader.fieldnames
                or []
            )
        )

        if missing_columns:

            raise ValueError(

                "Missing required columns: "
                f"{', '.join(sorted(missing_columns))}"
            )

        for row_number, row in enumerate(
            reader,
            start=2
        ):

            account_id = (
                row[
                    "AccountId"
                ]
                .strip()
            )

            role_arn = (
                row[
                    "Arn"
                ]
                .strip()
            )

            role_name = (
                row[
                    "Name"
                ]
                .strip()
            )

            if not account_id:

                raise ValueError(
                    f"Row {row_number}: "
                    f"AccountId is empty"
                )

            if not role_arn:

                raise ValueError(
                    f"Row {row_number}: "
                    f"Arn is empty"
                )

            if not role_name:

                raise ValueError(
                    f"Row {row_number}: "
                    f"Name is empty"
                )

            role_key = (
                account_id,
                role_arn
            )

            if role_key in seen_roles:

                raise ValueError(

                    f"Duplicate role detected: "
                    f"{account_id} | "
                    f"{role_arn}"
                )

            seen_roles.add(
                role_key
            )

            grouped_roles[
                account_id
            ].append({

                "account_id":
                account_id,

                "role_arn":
                role_arn,

                "role_name":
                role_name

            })

    return grouped_roles