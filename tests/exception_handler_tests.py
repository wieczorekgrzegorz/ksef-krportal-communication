import http.client as http_client
import unittest
from unittest.mock import patch

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH

from modules.utilities.exception_handler import handle_exception, QueryCosmosDBError

# turn off logs for testing
context.turn_off_logging(module="modules.utilities.exception_handler")


class TestHandleException(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {__name__}.{cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {__name__}.{cls.__name__} ###\n")

    def test_valid_input(self) -> None:
        """Test the function with valid input."""

        exc_name = "ValueError"
        exc_message = "Invalid input"
        exc_details = "Details"
        exc_status_code = http_client.BAD_REQUEST
        expected_result = (
            '{\n    "exception": "ValueError",\n    "message": "Invalid input",\n    "status_code": 400,\n    "details": "Details"\n}',
            http_client.BAD_REQUEST,
        )

        exc_to_test = QueryCosmosDBError(
            exception_type=exc_name,
            details=exc_details,
            message=exc_message,
            status_code=exc_status_code,
        )
        test_result = handle_exception(exc=exc_to_test)

        self.assertEqual(first=expected_result, second=test_result)

    def test_missing_fields(self) -> None:
        """Test the function with missing fields in the input by removing one of attributes."""

        exc_name = "QueryCosmosDBError"
        exc_message = "Unhandled exception."
        exc_details = "Unhandled exception."
        exc_status_code = http_client.INTERNAL_SERVER_ERROR
        expected_result = (
            '{\n    "exception": "QueryCosmosDBError",\n    "message": "Unhandled exception. Please contact system administrator.",\n    "status_code": "HTTPStatus.INTERNAL_SERVER_ERROR",\n    "details": "None"\n}',
            http_client.INTERNAL_SERVER_ERROR,
        )

        exc_to_test = QueryCosmosDBError(
            exception_type=exc_name,
            details=exc_details,
            message=exc_message,
            status_code=exc_status_code,
        )
        exc_to_test.__delattr__("status_code")

        test_result = handle_exception(exc=exc_to_test)

        self.assertEqual(first=expected_result, second=test_result)


if __name__ == "__main__":
    unittest.main()
