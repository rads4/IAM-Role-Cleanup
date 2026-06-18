# IAM Role Lifecycle Manager

IAM Role Lifecycle Manager is a Jenkins-driven automation tool for safely backing up, deleting, and restoring IAM roles across AWS accounts.

## Features

* Multi-account IAM role cleanup
* Pre-deletion role backup
* IAM role restore from backup
* Dry-run execution mode
* Slack notifications with backup attachments
* Detailed execution logging
* Error reporting and audit artifacts
* Jenkins pipeline integration
* Git-backed backup retention

## Repository Structure

```text
config/      Application configuration
inputs/      Role input files
modules/     Core application modules
backups/     Generated backup artifacts
main.py      IAM role deletion workflow
restore_roles.py  IAM role restore workflow
Jenkinsfile  CI/CD pipeline definition
```

## Supported Operations

### Delete Roles

Reads IAM roles from a CSV file, creates a backup, validates permissions, and performs deletion.

### Restore Roles

Restores IAM roles from previously generated backup files with support for:

* Full restore
* Account-level restore
* Role-level restore

## Execution Modes

* Dry Run
* Live Execution

## Notifications

Execution summaries, backup files, and error reports can be delivered through Slack and Jenkins artifacts.

## Requirements

* Python 3.x
* boto3
* slack_sdk
* AWS IAM permissions for role lifecycle operations
