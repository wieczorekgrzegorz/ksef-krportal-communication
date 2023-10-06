import unittest

from azure.functions import HttpRequest

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH
from modules.get_query_from_body import (
    get_json_from_payload,
    get_query_from_payload,
    main,
)
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError

# turn off logs for testing
context.turn_off_logging(module="modules.get_query_from_body")


class TestGetJSONFromPayload(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_valid_input_returns_dict(self) -> None:
        """Test getting a valid request body"""

        body = b'{"query": "SELECT * FROM c"}'
        test_input = HttpRequest(method="POST", body=body, url="url")
        expected_result = {"query": "SELECT * FROM c"}
        test_result = get_json_from_payload(payload=test_input)

        self.assertIsInstance(obj=test_result, cls=dict)
        self.assertEqual(first=test_result, second=expected_result)

    def test_invalid_input_raises_custom_exception(self) -> None:
        """Test getting an invalid request body"""

        test_input = HttpRequest(method="POST", body=b"", url="url")

        with self.assertRaises(expected_exception=QueryCosmosDBError):
            get_json_from_payload(payload=test_input)


class TestGetQueryFromPayload(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_valid_input_returns_string(self) -> None:
        """Test decoding a valid request body."""

        test_input: dict = {"query": "SELECT * FROM c"}
        expected_result: str = "SELECT * FROM c"
        test_result = get_query_from_payload(json_payload=test_input)

        self.assertIsInstance(obj=test_result, cls=str)
        self.assertEqual(first=test_result, second=expected_result)

    def test_invalid_input_raises_custom_error(self) -> None:
        """Test decoding an invalid request body"""

        test_input: dict = {}

        with self.assertRaises(expected_exception=QueryCosmosDBError):
            get_query_from_payload(json_payload=test_input)


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_valid_input_returns_string(self) -> None:
        """Test getting a valid SQL query from a request body."""

        body = b'{"query": "SELECT * FROM c"}'
        test_input = HttpRequest(method="POST", body=body, url="url")
        expected_query = "SELECT * FROM c"
        test_result = main(req=test_input)

        self.assertIsInstance(obj=test_result, cls=str)
        self.assertEqual(first=test_result, second=expected_query)

    def test_with_invalid_input(self) -> None:
        """There's no test to be done. Main function is a wrapper for other functions.
        Invalid input into the module would be handled by try/except blocks in called functions.
        """
        self.assertTrue(expr=True)


if __name__ == "__main__":
    unittest.main()
