import json
import unittest
from unittest.mock import patch

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError

# turn off logs for testing
context.turn_off_logging(module="modules.utilities.query_cosmosDB_error")


class TestQueryCosmosDBError(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.mocked_exception_type = "test_exception"
        cls.mocked_details = "test_details"
        cls.mocked_message = "test_message"
        cls.mocked_status_code = 123

        with patch("modules.utilities.query_cosmosDB_error.log").start() as mock_logger:
            cls.mock_logger = mock_logger
            cls.mock_logger.setLevel.return_value = None

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_correct_attributes_assignment(self) -> None:
        exception = QueryCosmosDBError(
            exception_type=self.mocked_exception_type,
            details=self.mocked_details,
            message=self.mocked_message,
            status_code=self.mocked_status_code,
        )

        self.assertEqual(
            first=exception.exception_type, second=self.mocked_exception_type
        )
        self.assertEqual(first=exception.details, second=self.mocked_details)
        self.assertEqual(first=exception.message, second=self.mocked_message)
        self.assertEqual(first=exception.status_code, second=self.mocked_status_code)

    def test_build_error_response_input_compatible(self) -> None:
        exception = QueryCosmosDBError(
            exception_type=self.mocked_exception_type,
            details=self.mocked_details,
            message=self.mocked_message,
            status_code=self.mocked_status_code,
        )
        actual_response = exception.error_response

        expected_response_dict = {
            "exception": self.mocked_exception_type,
            "message": self.mocked_message,
            "status_code": self.mocked_status_code,
            "details": self.mocked_details,
        }
        expected_response = json.dumps(
            obj=expected_response_dict,
            indent=4,
            sort_keys=False,
            ensure_ascii=False,
        )

        self.assertEqual(first=actual_response, second=expected_response)

    def test_build_error_response_with_non_jsonable_inputs(self) -> None:
        """Test building error response with input that can't be converted to json"""
        exception = QueryCosmosDBError(
            exception_type="ValueError",
            details=set([1, 2, 3]),  # type: ignore # TypeIssue is the point of this test
            message="An error occurred",
            status_code=400,
        )
        expected_response_dict = {
            "exception": "ValueError",
            "message": "An error occurred",
            "status_code": "400",
            "details": "{1, 2, 3}",
        }

        expected_response = json.dumps(
            obj=expected_response_dict,
            indent=4,
            sort_keys=False,
            ensure_ascii=False,
        )
        actual_response = exception.error_response

        self.assertEqual(first=actual_response, second=expected_response)

    def test_str(self) -> None:
        """Test __str__ method."""
        exception = QueryCosmosDBError(
            exception_type="ValueError",
            details="Invalid value",
            message="An error occurred",
            status_code=400,
        )
        expected_str = "QueryCosmosDBError for passed ValueError exception"
        actual_str = str(object=exception)

        self.assertEqual(first=actual_str, second=expected_str)


if __name__ == "__main__":
    unittest.main()
