# Multi Account IAM Role Cleanup - Backup & Restore

## Overview

This branch extends the IAM Role Cleanup utility with backup and restoration capabilities while introducing support for multi-account execution.

Before any IAM role is deleted, the script captures the complete role configuration and stores it in a backup file. The backup can later be used to recreate deleted roles, restoring trust policies, managed policies, inline policies, and optional instance profile associations.

The current implementation is designed for local execution using AWS profiles. Jenkins orchestration and cross-account AssumeRole execution are intentionally excluded from this branch and will be implemented separately.

---

## Features

| Capability                     | Supported |
| ------------------------------ | --------- |
| Single Account Execution       | ✅         |
| Multi-Account Execution        | ✅         |
| Automatic Backup Before Delete | ✅         |
| Role Restoration               | ✅         |
| Parallel Account Processing    | ✅         |
| Parallel Role Processing       | ✅         |
| Profile-Based Authentication   | ✅         |
| Automatic Profile Creation     | ✅         |
| Interactive Execution          | ✅         |
| Interactive Restore Workflow   | ✅         |
| Dry Run Support                | ✅         |

---

## Architecture

![Architecture](docs/architecture-multi-account-backup-and-restore.png)

---

## Execution Flow

### Cleanup Flow (Backup + Delete)

```text
Role CSV
    │
    ▼
Load Account Mapping
    │
    ▼
Create / Resolve AWS Profiles
    │
    ▼
Process Accounts In Parallel
    │
    ▼
Process Roles In Parallel
    │
    ▼
Capture Role Metadata
    │
    ▼
Persist Backup
    │
    ▼
Detach Policies
    │
    ▼
Remove Instance Profile Associations
    │
    ▼
Delete IAM Role
```

### Restore Flow

```text
Select Backup File
    │
    ▼
Select Restore Mode
    │
    ▼
Select Account(s)
    │
    ▼
Select Role(s)
    │
    ▼
Recreate IAM Role
    │
    ▼
Attach Managed Policies
    │
    ▼
Restore Inline Policies
    │
    ▼
(Optional) Restore Instance Profiles
```

---

## Input Files

### Role Input File

Used to identify roles that should be processed.

```text
dummy-inputs/
└── poc_roles.csv

inputs/
└── roles.csv
```

Example:

```csv
AccountId,AccountCategory,Type,Name
123456789012,POC,Role,ExampleRole
```

---

### Account Credential File

Used to create local AWS profiles automatically.

```text
inputs/
├── account_credentials.csv
└── account_credentials.csv.example
```

Example:

```csv
AccountId,AccessKeyId,SecretAccessKey,Region,Permission
123456789012,XXXXXXXX,XXXXXXXX,ap-south-1,admin
```

Generated profile format:

```text
<AccountId>-<Permission>
```

Example:

```text
123456789012-admin
```

---

## Backup Structure

A single backup file is generated per execution.

The backup contains:

* Backup metadata
* Account information
* Role definitions
* Trust policies
* Managed policy attachments
* Inline policies
* Instance profile associations

Example structure:

```json
{
  "backup_metadata": {
    "created_at": "...",
    "total_accounts": 2,
    "total_roles": 25
  },
  "accounts": {
    "123456789012": {
      "roles": {}
    },
    "987654321098": {
      "roles": {}
    }
  }
}
```

---

## Parallel Processing Model

### Account-Level Parallelism

Multiple AWS accounts can be processed simultaneously.

```text
Account A
Account B
Account C
```

run in parallel.

### Role-Level Parallelism

Within each account, IAM roles are processed concurrently.

```text
Role 1
Role 2
Role 3
Role 4
```

run in parallel.

This significantly reduces execution time for large cleanup operations.

---

## Running Cleanup

```bash
python3 main.py
```

The utility provides an interactive workflow for:

* Selecting role input file
* Selecting credential file
* Creating required profiles
* Executing backup and deletion

No command-line arguments are required.

---

## Running Restore

```bash
python3 restore_roles.py
```

The utility provides an interactive workflow for:

* Selecting backup file
* Selecting restore mode
* Selecting accounts
* Selecting roles
* Choosing instance profile restoration
* Running in dry-run mode if required

No command-line arguments are required.

---

## Dry Run

Dry run mode allows validation without making changes.

Supported for:

* Cleanup execution
* Restore execution

This is recommended before performing operations in production environments.

---

## Output Artifacts

### Backup Files

```text
backups/
```

Generated before any deletion activity.

### Error Reports

```text
output/
```

Generated when failures occur during backup, deletion, or restoration.

---

## Local Testing

POC testing can be performed using:

```text
dummy-inputs/poc_roles.csv
```

along with a corresponding credentials file.

This allows validation of:

* Backup generation
* Role deletion
* Role restoration
* Multi-account processing logic
* Profile creation workflow

without requiring Jenkins integration.

---

## Out of Scope

The following capabilities are intentionally excluded from this branch:

* Jenkins integration
* Operator account orchestration
* Cross-account AssumeRole execution
* Automatic cleanup role provisioning
* CloudFormation-based deployment workflows

These features will be implemented in a dedicated Jenkins / AssumeRole branch.

---

## Safety Controls

* Backup captured before deletion
* Dry-run support
* Retry handling for throttling
* Error reporting with CSV output
* Role existence validation during restore
* Thread-safe backup persistence
* Account-level isolation during execution
