import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


class GitBackupManager:

    def __init__(
        self,
        logger,
        backup_branch="iam-role-cleaner-backups",
        repo_path="."
    ):

        self.logger = logger
        self.backup_branch = backup_branch
        self.repo_path = Path(repo_path)

    def _run(self, cmd):

        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            self.logger.error(result.stderr)

            raise Exception(
                f"Git command failed: {cmd}"
            )

        return result.stdout.strip()

    def commit_backup_files(
        self,
        backup_file,
        metadata_file,
        error_file=None
    ):

        try:

            timestamp = datetime.utcnow().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            backup_dir = self.repo_path / "backups"

            backup_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            # Create structured folder
            target_dir = (
                backup_dir / timestamp
            )

            target_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            # Copy files into git folder
            files_to_copy = [
                backup_file,
                metadata_file
            ]

            if error_file:

                files_to_copy.append(
                    error_file
                )

            for file_path in files_to_copy:

                if file_path and Path(file_path).exists():

                    shutil.copy2(
                        file_path,
                        target_dir
                    )

            # Git operations
            self._run(
                ["git", "checkout", self.backup_branch]
            )

            self._run(
                ["git", "add", "."]
            )

            commit_message = (
                f"backup: iam role cleaner "
                f"{timestamp}"
            )

            self._run(
                ["git", "commit", "-m", commit_message]
            )

            self._run(
                ["git", "push", "origin", self.backup_branch]
            )

            self.logger.info(
                "Backup successfully pushed to GitLab branch"
            )

        except Exception as error:

            self.logger.error(
                f"Git backup failed: {str(error)}"
            )