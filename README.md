# Jenkins Assume-Role Approach

Multi-account IAM Role Backup, Deletion, and Restore Utility using AWS STS AssumeRole.

---

## Overview

This branch implements and validates a **Jenkins AssumeRole-based IAM cleanup workflow**.

The solution is designed for environments where a Jenkins job (or an operator running locally with equivalent permissions) must perform IAM role cleanup across multiple AWS accounts in a controlled and auditable manner.

The workflow follows a two-step role assumption model:

1. Assume an existing cross-account role in the target account.
2. Create or validate a dedicated cleanup role (`iam-role-cleaner`).
3. Assume the cleanup role.
4. Backup role configuration.
5. Delete the target role.
6. Restore roles later from backup if required.

Although the intended execution environment is Jenkins, the complete workflow has been developed and tested locally to validate functionality before Jenkins integration.

---

## Architecture

> Architecture diagram placeholder

```text
docs/jenkins-assume-role-arch.png
```

### Execution Flow

```text
Local Execution / Jenkins Job
                │
                ▼
Existing Cross-Account Role
(user supplied)
                │
                ▼
iam-role-cleaner
(create / validate)
                │
                ▼
Assume iam-role-cleaner
                │
                ▼
Backup Role Metadata
                │
                ▼
Delete IAM Role
```

### Intended Jenkins Flow

```text
Jenkins Job
      │
      ▼
Assume Existing Cross-Account Role
      │
      ▼
Validate/Create iam-role-cleaner
      │
      ▼
Assume iam-role-cleaner
      │
      ▼
Backup + Delete + Restore Operations
```

---

## Features

### Multi-Account Processing

Processes IAM roles across multiple AWS accounts concurrently.

### Jenkins-Oriented AssumeRole Workflow

Designed around a Jenkins execution model where access to target accounts is obtained through an existing cross-account role.

The role name is supplied at runtime and used to establish initial access into each target account.

Examples:

```text
terraform-assume-role
platform-assume-role
non-prod-assume-role
```

### Safe Backup

Captures and stores:

- Trust Policy
- Managed Policies
- Inline Policies
- Instance Profiles
- Description
- Path
- Max Session Duration

before deletion.

### Restore Capability

Deleted roles can be restored from generated backup files.

### Concurrency

Supports:

- Account-level parallelism
- Role-level parallelism

for faster execution.

### Automatic Cleaner Role Validation

The utility validates:

- Cleaner role existence
- Trust policy configuration
- Permission policy configuration

before role deletion begins.

### Retry Logic

Automatic retry handling for:

- Throttling
- Request limits
- Delete conflicts
- Concurrent modifications

using exponential backoff.

### Detailed Error Reporting

Generates structured error reports containing:

- Account ID
- Role Name
- Failure Stage
- Error Type
- Error Message

---

## Project Structure

```text
.
├── config/
├── modules/
├── tests/
├── docs/
├── inputs/
├── backups/
├── output/
│
├── main.py
├── restore_roles.py
│
├── create_poc_roles.py
├── create_jenkins_poc_roles.py
│
├── cleaner-policy.json
├── cleaner-trust.json
├── trust-policy.json
│
├── requirements.txt
└── README.md
```

---

## Input Format

### Role Cleanup CSV

```csv
AccountId,Arn,Name
123456789012,arn:aws:iam::123456789012:role/ExampleRole,ExampleRole
```

Required fields:

| Column    | Description    |
| --------- | -------------- |
| AccountId | AWS Account ID |
| Arn       | IAM Role ARN   |
| Name      | IAM Role Name  |

---

## Cleanup Workflow

### Step 1

Launch the utility.

```bash
python3 main.py
```

### Step 2

Select the role input CSV.

Example:

```text
Available Role CSV Files:

1. jenkins_poc_roles.csv
2. roles.csv
```

### Step 3

Provide the existing cross-account role name.

Example:

```text
terraform-assume-role
```

This role acts as the bootstrap role used to gain access to each target account.

### Step 4

The utility performs the following sequence:

```text
Assume Cross-Account Role
          ↓
Validate/Create iam-role-cleaner
          ↓
Assume iam-role-cleaner
          ↓
Backup Roles
          ↓
Delete Roles
```

---

## Runtime Parameters

The utility currently requires the following runtime inputs:

| Parameter               | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| Role Cleanup CSV        | CSV containing target accounts and IAM roles         |
| Cross-Account Role Name | Existing role used to gain access to target accounts |

Example:

```text
Cross Account Role:
terraform-assume-role
```

The supplied role name is used to dynamically construct the target role ARN:

```text
arn:aws:iam::<ACCOUNT_ID>:role/<CROSS_ACCOUNT_ROLE_NAME>
```

---

## Restore Workflow

Restore previously deleted roles from backup.

```bash
python3 restore_roles.py
```

Supported restore modes:

```text
1. All Accounts → All Roles
2. All Accounts → Selected Roles
3. Selected Account → All Roles
4. Selected Account → Selected Roles
```

---

## Backup Format

Backups are stored as JSON.

Location:

```text
backups/
```

Example:

```json
{
  "accounts": {
    "123456789012": {
      "roles": {
        "ExampleRole": {
          ...
        }
      }
    }
  }
}
```

---

## Error Reports

Location:

```text
output/role_deletion_errors.csv
```

Example:

```csv
timestamp,account_id,role_name,stage,error_type,error_message
```

---

## Cleaner Role

The utility manages a dedicated cleanup role:

```text
iam-role-cleaner
```

Responsibilities:

- Backup IAM Roles
- Detach Managed Policies
- Delete Inline Policies
- Remove Instance Profiles
- Delete IAM Roles
- Restore Deleted Roles

The role is automatically created or validated before cleanup operations begin.

---

## Configuration

Located in:

```text
config/settings.py
```

Key parameters:

```python
ACCOUNT_WORKERS = 3

ROLE_WORKERS = 10

MAX_RETRY_ATTEMPTS = 5

BASE_BACKOFF_SECONDS = 1

DRY_RUN = False
```

---

## Testing Utilities

### Generate POC Roles

```bash
python3 create_poc_roles.py
```

Creates sample IAM roles for testing.

### Generate Jenkins Cleanup Dataset

```bash
python3 create_jenkins_poc_roles.py
```

Creates:

- Test IAM Roles
- Cleanup CSV

for end-to-end validation.

---

## Validation Performed

Before deletion:

```text
✓ Cross-account role assumption
✓ Account validation
✓ Cleaner role existence
✓ Cleaner trust policy validation
✓ Cleaner permission validation
✓ Backup creation
```

---

## Testing Status

This implementation has been validated through local execution using AWS AssumeRole workflows.

The following capabilities have been tested:

```text
✓ Multi-account processing
✓ Cross-account role assumption
✓ Cleaner role creation
✓ Cleaner role validation
✓ IAM role backup
✓ IAM role deletion
✓ IAM role restoration
✓ Error reporting
✓ Concurrent execution
```

The same workflow is intended to be executed from Jenkins once the dedicated Jenkins infrastructure and execution environment are provisioned.

---

## Branch Scope

This branch represents the **Jenkins AssumeRole approach** currently under development and validation.

Architecture implemented in this branch:

```text
Jenkins Job / Local Execution
                │
                ▼
Existing Cross-Account Role
(user supplied)
                │
                ▼
iam-role-cleaner
                │
                ▼
Backup + Delete + Restore
```

Key characteristics:

- Uses an existing cross-account role supplied at runtime.
- Creates or validates `iam-role-cleaner` in target accounts.
- Performs cleanup operations through the dedicated cleaner role.
- Fully tested through local execution.
- Intended to be migrated to Jenkins execution without changing the core workflow.

Future iterations may replace the bootstrap role dependency with a dedicated Jenkins execution role and CloudFormation-managed deployment of `iam-role-cleaner` across target accounts.
