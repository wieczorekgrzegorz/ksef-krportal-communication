from collections.abc import Iterable
import http.client as http_client
from typing import Any
import unittest
from unittest.mock import MagicMock, Mock, patch

from azure.cosmos import exceptions as cosmos_exc, ContainerProxy

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH

from modules.query_cosmosDB import main, iterable_to_dict, dict_to_json, get_query_items
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError

# turn off logs for testing
context.turn_off_logging(module="modules.query_cosmosDB")


class TestGetQueryItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.container_mock = Mock(spec=ContainerProxy)
        cls.sql_query = "mock query"
        cls.expected_exception = QueryCosmosDBError

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_returning_valid_iterable(self) -> None:
        """Tests the function with valid input."""

        container = MagicMock()
        mock_query_items: Iterable[dict[str, Any]] = [
            {"id": 1, "name": "item1"},
            {"id": 2, "name": self.setUp},
        ]
        container.query_items.return_value = mock_query_items

        test_output = get_query_items(container=container, sql_query=self.sql_query)

        self.assertIsInstance(obj=test_output, cls=Iterable)
        self.assertEqual(first=mock_query_items, second=test_output)

    def test_raising_custom_exception_from_cosmos_resource_not_found_error(
        self,
    ) -> None:
        """Tests function raising custom exception when CosmosDB container is not found."""

        self.container_mock.query_items.side_effect = (
            cosmos_exc.CosmosResourceNotFoundError(
                message="Container not found", status_code=404
            )
        )

        with self.assertRaises(expected_exception=self.expected_exception):
            get_query_items(container=self.container_mock, sql_query=self.sql_query)

    def test_raising_custom_exception_from_http_response_error(
        self,
    ) -> None:
        """Tests function raising custom exception when CosmosDB query fails."""

        self.container_mock.query_items.side_effect = (
            cosmos_exc.CosmosHttpResponseError(message="Query failed", status_code=500)
        )

        with self.assertRaises(expected_exception=self.expected_exception):
            get_query_items(container=self.container_mock, sql_query=self.sql_query)

    def test_test_raising_custom_exception_from_timeout_error(self) -> None:
        """Tests function raising custom exception when CosmosDB query times out."""

        self.container_mock.query_items.side_effect = (
            cosmos_exc.CosmosClientTimeoutError()
        )

        with self.assertRaises(expected_exception=self.expected_exception):
            get_query_items(container=self.container_mock, sql_query=self.sql_query)


class TestIterableToDict(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_returning_dict(self) -> None:
        """Tests the function with valid input."""
        test_input = iter(({"id": "1", "name": "item1"}, {"id": "2", "name": "item2"}))

        expected_outcome = {
            "1": {"id": "1", "name": "item1"},
            "2": {"id": "2", "name": "item2"},
        }
        actual_outcome = iterable_to_dict(iterable=test_input)

        self.assertIsInstance(obj=actual_outcome, cls=dict)
        self.assertEqual(
            first=actual_outcome,
            second=expected_outcome,
        )

    def test_raising_custom_exception(self) -> None:
        """Tests function raising custom exception when items in Iterable don't have 'id' field."""
        expected_exc = QueryCosmosDBError
        iterable = iter(
            [
                {"not_id": "1", "name": "item1"},
                {"not_id": "2", "name": "item2"},
            ]
        )

        with self.assertRaises(expected_exception=expected_exc):
            iterable_to_dict(iterable=iterable)


class TestDictToJson(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_returniung_json_string(self) -> None:
        """Tests the function with valid input."""
        query_items_dict = {
            "1": {"id": "1", "name": "item1"},
            "2": {"id": "2", "name": "item2"},
        }
        expected_outcome = '{\n    "1": {\n        "id": "1",\n        "name": "item1"\n    },\n    "2": {\n        "id": "2",\n        "name": "item2"\n    }\n}'
        actual_outcome = dict_to_json(query_items_dict=query_items_dict)

        self.assertIsInstance(obj=actual_outcome, cls=str)
        self.assertEqual(
            first=actual_outcome,
            second=expected_outcome,
        )

    def test_raising_custom_exception(self) -> None:
        """Tests function raising custom exception when any of either key or value of passed dictionary
        can't be converted to json."""
        expected_exc = QueryCosmosDBError
        query_items_dict = {
            "1": set([1, 2, 3]),
            "2": {"not_id": "2", "name": "item2"},
        }

        with self.assertRaises(expected_exception=expected_exc):
            dict_to_json(query_items_dict=query_items_dict)


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.container_mock = Mock(spec=ContainerProxy)
        cls.sql_query = "mock query"

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_with_valid_input(self) -> None:
        """Tests the main function with valid input."""
        query_items_list = [{"id": "1", "name": "item1"}, {"id": "2", "name": "item2"}]
        self.container_mock.query_items.return_value = query_items_list

        expected_outcome = (
            str(
                '{\n    "1": {\n        "id": "1",\n        "name": "item1"\n    },\n    "2": {\n        "id": "2",\n        "name": "item2"\n    }\n}'
            ),
            http_client.OK,
        )

        actual_outcome = main(container=self.container_mock, sql_query=self.sql_query)

        self.assertIsInstance(obj=actual_outcome, cls=tuple)
        self.assertEqual(first=actual_outcome, second=expected_outcome)

    def test_with_no_query_items_returned(self) -> None:
        """Tests the main function when query returns no items."""
        query_items_list = []
        self.container_mock.query_items.return_value = query_items_list

        expected_outcome = "Query returned no items.", http_client.OK

        actual_outcome = main(container=self.container_mock, sql_query=self.sql_query)

        self.assertIsInstance(obj=actual_outcome, cls=tuple)
        self.assertEqual(first=actual_outcome, second=expected_outcome)


if __name__ == "__main__":
    unittest.main()
