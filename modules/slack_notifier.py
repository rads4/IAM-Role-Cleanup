from pathlib import Path

from slack_sdk import WebClient

from slack_sdk.errors import (
    SlackApiError
)


class SlackNotifier:

    def __init__(
        self,
        token,
        channel_id,
        logger
    ):

        self.client = (
            WebClient(
                token=token
            )
        )

        self.channel_id = (
            channel_id
        )

        self.logger = logger

    def send_summary(

        self,

        action,

        dry_run,

        accounts,

        roles,

        build_number,

        build_url
    ):

        message = f"""
*IAM ROLE CLEANER*

*Action:* {action}
*Dry Run:* {dry_run}

*Accounts:* {accounts}
*Roles:* {roles}

*Build Number:* {build_number}
*Build URL:* {build_url}
"""

        try:

            self.client.chat_postMessage(

                channel=
                self.channel_id,

                text=
                message
            )

            self.logger.info(
                "Slack summary sent"
            )

        except SlackApiError as error:

            self.logger.error(

                f"Slack summary failed: "
                f"{str(error)}"
            )

    def upload_file(
        self,
        file_path,
        title
    ):

        file_path = str(
            file_path
        )

        if not Path(
            file_path
        ).exists():

            return

        try:

            self.client.files_upload_v2(

                channel=
                self.channel_id,

                file=
                file_path,

                title=
                title
            )

            self.logger.info(

                f"Slack upload success: "
                f"{file_path}"
            )

        except SlackApiError as error:

            self.logger.error(

                f"Slack upload failed: "
                f"{file_path} | "
                f"{str(error)}"
            )

    def upload_backup_bundle(

        self,

        backup_file,

        metadata_file,

        error_csv=None,

        account_summary_csv=None
    ):

        self.upload_file(

            backup_file,

            "Role Backup JSON"
        )

        self.upload_file(

            metadata_file,

            "Backup Metadata"
        )

        if error_csv:

            self.upload_file(

                error_csv,

                "Role Errors"
            )

        if account_summary_csv:

            self.upload_file(

                account_summary_csv,

                "Account Error Summary"
            )