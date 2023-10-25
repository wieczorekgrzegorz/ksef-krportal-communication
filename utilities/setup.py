"""Holds environmental variables, sets up custom logger."""

import logging
import os

log = logging.getLogger(name="log")

# declare environment constants
COSMOSDB_CONNECTION_STRING: str = os.environ["COSMOSDB_CONNECTION_STRING"]
COSMOSDB_DATABASE_ID: str = os.environ["COSMOSDB_DATABASE_ID"]
COSMOSDB_CONTAINER_ID: str = os.environ["COSMOSDB_CONTAINER_ID"]
BLOB_SERVICE_CONNECTION_STRING: str = os.environ["BLOB_CONNECTION_STRING"]
BLOB_CONTAINER_NAME: str = os.environ["BLOB_CONTAINER_NAME"]


def logger(
    logging_format: str = "%(levelname)s, %(name)s.%(funcName)s: %(message)s",
    level: int = logging.INFO,
) -> None:
    """
    Sets up custom logger.

    Parameters:
        format (str, optional): Logging format. Defaults to "%(name)s%(funcName)s: %(message)s".
        level (int, optional): Logging level. Defaults to logging.INFO.

    Returns:
        None
    """
    log.debug(msg="Setting up custom logger.")

    log.setLevel(level=level)

    handler = logging.StreamHandler(stream=None)

    formatter = logging.Formatter(fmt=logging_format)
    handler.setFormatter(fmt=formatter)

    if log.hasHandlers():
        log.handlers.clear()

    log.addHandler(handler)
