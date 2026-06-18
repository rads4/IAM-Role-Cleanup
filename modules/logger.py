import logging


class SeparatorFilter(
    logging.Filter
):

    def filter(
        self,
        record
    ):

        return True


def get_logger():

    logger = logging.getLogger(
        "iam-role-cleaner"
    )

    if logger.handlers:

        return logger

    logger.setLevel(
        logging.INFO
    )

    handler = logging.StreamHandler()

    formatter = logging.Formatter(

        "%(asctime)s | "
        "%(levelname)-8s | "
        "%(threadName)-20s | "
        "%(message)s"
    )

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )

    logger.propagate = False

    return logger


def print_banner(
    logger,
    title
):

    logger.info(
        "=" * 100
    )

    logger.info(
        title
    )

    logger.info(
        "=" * 100
    )


def print_account_header(
    logger,
    account_id
):

    logger.info(
        "=" * 100
    )

    logger.info(
        f"ACCOUNT : "
        f"{account_id}"
    )

    logger.info(
        "=" * 100
    )


def print_role_header(
    logger,
    account_id,
    role_name,
    role_arn=None
):

    logger.info(
        "-" * 100
    )

    logger.info(
        f"ACCOUNT_ID : "
        f"{account_id}"
    )

    logger.info(
        f"ROLE_NAME  : "
        f"{role_name}"
    )

    if role_arn:

        logger.info(
            f"ROLE_ARN   : "
            f"{role_arn}"
        )

    logger.info(
        "-" * 100
    )