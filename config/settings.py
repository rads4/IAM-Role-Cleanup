ACCOUNT_WORKERS = 3

ROLE_WORKERS = 10

MAX_RETRY_ATTEMPTS = 5

BASE_BACKOFF_SECONDS = 1

ERROR_REPORT_PREFIX = (
    "role_deletion_errors"
)

DRY_RUN = False

BACKUP_DIR = "backups"

OUTPUT_DIR = "output"

CLEANER_ROLE_NAME = (
    "iam-role-cleaner"
)

CLEANER_POLICY_NAME = (
    "iam-role-cleaner-policy"
)

ASSUME_ROLE_SESSION_NAME = (
    "iam-cleanup-session"
)
