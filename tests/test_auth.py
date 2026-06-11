from modules.auth import get_account_session

session = get_account_session(
    "851043415728"
)

sts = session.client("sts")

print(
    sts.get_caller_identity()
)