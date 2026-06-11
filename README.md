# IAM Role Cleanup Utility

## Overview

This utility automates IAM role cleanup within an AWS account using a CSV-based input. It reads the list of IAM roles, processes them in parallel, and removes associated dependencies before deleting the roles.

The solution was built to support large-scale IAM cleanup activities while maintaining safety, visibility, and error reporting.

## Features

* CSV-driven role processing
* Parallel role execution using configurable worker threads
* Automatic removal of:

  * Managed policy attachments
  * Inline policies
  * Instance profile associations
* Exponential backoff for throttling scenarios
* Error reporting through CSV export
* Dry-run support for validation before execution
* Account verification before execution

## Project Structure

config/

* Application configuration

modules/

* Authentication
* CSV parsing
* IAM cleanup logic
* Execution engine
* Logging
* Error collection

tests/

* Validation utilities

main.py

* Application entry point

## Execution Flow

1. Authenticate using an AWS profile.
2. Validate the connected AWS account.
3. Read role information from the input CSV.
4. Process roles using configurable parallel workers.
5. Remove dependencies associated with each role.
6. Delete roles.
7. Generate an error report for failed operations.

## Configuration

Key settings are managed through:

config/settings.py

Examples:

* AWS Profile
* Dry Run Mode
* Worker Counts
* Retry Settings
* Input CSV Path

## Running the Utility

Validate execution:

```bash
python3 main.py
```

For safety, begin with:

```python
DRY_RUN = True
```

After validation:

```python
DRY_RUN = False
```

## Error Reporting

Failures are captured in:

output/role_deletion_errors.csv

This report includes:

* Account ID
* Role Name
* Error Type
* Error Message

## Current Implementation

The current implementation is designed for profile-based execution against a single AWS account.

Future enhancements may introduce cross-account execution using AWS STS AssumeRole and multi-account orchestration.
