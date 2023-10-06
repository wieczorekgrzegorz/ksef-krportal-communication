# type: ignore # Pylance returns fake-negative import error. Imports here are used as context for unit tests.
# flake8: noqa: F401, F402 # imports in this file are used in other files
"""Context file for unit tests. 
Mocks environment variables and inserts main app folder to PATH.
Turns off logging for tested modules.
"""
import logging
import os
from pathlib import PurePath as path
import sys
from unittest.mock import patch

function_app_path = str(path(__file__).parents[1])

# adding main app folder to PATH
sys.path.insert(0, function_app_path)


# define global variables for tests
# Reason: So every test uses same mock values for environment variables
# Reason 2: tests would fail with KeyError("AZURE_COSMOSDB_CONNECTION_STRING")
#           exception when importing function_app
os.environ["AZURE_COSMOSDB_CONNECTION_STRING"] = "mock_connection_string"
os.environ["DATABASE_ID"] = "mock_database_id"
os.environ["CONTAINER_ID"] = "mock_container_id"


def turn_off_logging(module: str) -> None:
    """Turns off logging for tested modules."""
    logger_name = module + ".log"
    with patch(logger_name).start() as mock_logger:
        mock_logger = mock_logger
        mock_logger.setLevel.return_value = None


turn_off_logging(module="modules.utilities.exception_handler")
