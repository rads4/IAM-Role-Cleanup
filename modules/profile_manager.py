import configparser
from pathlib import Path


AWS_DIR = (
    Path.home() / ".aws"
)

CREDENTIALS_FILE = (
    AWS_DIR / "credentials"
)

CONFIG_FILE = (
    AWS_DIR / "config"
)


def profile_exists(
    profile_name
):

    credentials = (
        configparser.ConfigParser()
    )

    credentials.read(
        CREDENTIALS_FILE
    )

    return (
        profile_name
        in credentials.sections()
    )


def create_profile(
    profile_name,
    access_key,
    secret_key,
    region
):

    AWS_DIR.mkdir(
        exist_ok=True
    )

    credentials = (
        configparser.ConfigParser()
    )

    credentials.read(
        CREDENTIALS_FILE
    )

    if (
        profile_name
        not in credentials.sections()
    ):

        credentials[
            profile_name
        ] = {

            "aws_access_key_id":
            access_key,

            "aws_secret_access_key":
            secret_key
        }

        with open(
            CREDENTIALS_FILE,
            "w"
        ) as file:

            credentials.write(
                file
            )

    config = (
        configparser.ConfigParser()
    )

    config.read(
        CONFIG_FILE
    )

    config_section = (
        f"profile {profile_name}"
    )

    if (
        config_section
        not in config.sections()
    ):

        config[
            config_section
        ] = {

            "region": region,

            "output": "json"
        }

        with open(
            CONFIG_FILE,
            "w"
        ) as file:

            config.write(
                file
            )