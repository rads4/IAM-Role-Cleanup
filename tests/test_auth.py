from modules.auth import (
    get_account_session
)

session = get_account_session()

print(
    session.client(
        "sts"
    ).get_caller_identity()
)