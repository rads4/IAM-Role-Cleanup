import logging


def get_logger():

    logger = logging.getLogger("iam-role-delete")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(threadName)-12s | %(message)s"
    )

    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger