ACCOUNT_WORKERS = 3

ROLE_WORKERS = 10

MAX_RETRY_ATTEMPTS = 5

BASE_BACKOFF_SECONDS = 1

ERROR_REPORT_PREFIX = (
    "role_deletion_errors"
)

BACKUP_DIR = "backups"

OUTPUT_DIR = "output"

CLEANER_ROLE_NAME = (
    "ck-iam-role-cleaner"
)

CLEANER_POLICY_NAME = (
    "iam-role-cleaner-policy"
)

ASSUME_ROLE_SESSION_NAME = (
    "iam-cleanup-session"
)

JENKINS_MASTER_ROLE_ARN = (
    "arn:aws:iam::685502069032:role/"
    "ck-ops-jenkins-master-instance-iam-role"
)

SLACK_ENABLED = True