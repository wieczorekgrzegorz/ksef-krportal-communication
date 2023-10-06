import unittest
from unittest.mock import MagicMock, patch
import http.client as http_client

from azure.core import exceptions as azure_exc
from azure.cosmos import exceptions as cosmos_exc, ContainerProxy

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH
from modules.connection_setup import (
    setup_container_client,
    setup_cosmos_client,
    setup_database_client,
    main,
)
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError


# turn off logs for testing
context.turn_off_logging(module="modules.connection_setup")


class TestSetupCosmosClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.exception = QueryCosmosDBError
        cls.connection_string = "mock_connection_string"

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    @patch("modules.connection_setup.CosmosClient")
    def execute_assert_raises(self, mock_cosmos_client) -> None:
        """Helper function to execute the assertRaises block."""

        mock_cosmos_client.from_connection_string.side_effect = self.exc
        with self.assertRaises(expected_exception=self.exception) as cm:
            setup_cosmos_client(connection_string=self.connection_string)

            self.assertEqual(
                first=cm.exception.status_code, second=self.expected_status_code
            )
            self.assertEqual(
                first=cm.exception.message,
                second=self.expected_message,
            )
            self.assertEqual(
                first=cm.exception.exception_type,
                second=self.expected_exception_type,
            )
            self.assertEqual(first=cm.exception.details, second=self.expected_details)

    @patch("modules.connection_setup.CosmosClient")
    def test_successful_connection(self, mock_cosmos_client) -> None:
        """Test the function with a successful connection."""

        mock_client = MagicMock()
        mock_cosmos_client.from_connection_string.return_value = mock_client
        result = setup_cosmos_client(connection_string=self.connection_string)

        self.assertEqual(first=result, second=mock_client)

    def test_invalid_connection_string(self) -> None:
        """Test the function with an invalid connection string."""

        exc_message = "Failed to connect."
        self.exc = azure_exc.ServiceRequestError(message=exc_message)
        self.expected_message = "Failed to connect with host declared in AccountEndpoint. Check connection string."
        self.expected_exception_type = "ServiceRequestError"
        self.expected_details = exc_message
        self.expected_status_code = http_client.NOT_FOUND

        self.execute_assert_raises()

    def test_invalid_host_url(self) -> None:
        """Test the function with an invalid host URL."""

        exc_status_code = http_client.UNAUTHORIZED
        exc_message = "Invalid host URL."
        self.exc = cosmos_exc.CosmosResourceNotFoundError(
            message=exc_message,
            status_code=exc_status_code,
        )
        self.expected_message = "CosmosDB host URL is invalid. Check connection string."
        self.expected_exception_type = "CosmosResourceNotFoundError"
        self.expected_details = "Status code: 0\nInvalid host URL."
        self.expected_status_code = exc_status_code

        self.execute_assert_raises()

    def test_request_timeout(self) -> None:
        """Test the function with a request timeout."""

        self.exc = cosmos_exc.CosmosClientTimeoutError()
        self.expected_status_code = http_client.REQUEST_TIMEOUT
        self.expected_message = "Request timeout."
        self.expected_exception_type = "CosmosClientTimeoutError"
        self.expected_details = (
            "Client operation failed to complete within specified timeout."
        )

        self.execute_assert_raises()

    def test_unauthorized_request(self) -> None:
        """Test the function with an unauthorized request."""

        exc_status_code = http_client.UNAUTHORIZED
        exc_message = "Unauthorized request."

        self.exc = cosmos_exc.CosmosHttpResponseError(
            message=exc_message,
            status_code=exc_status_code,
        )
        self.expected_message = "Unauthorized. The input authorization token can't serve the request. Check connection string."
        self.expected_exception_type = "CosmosHttpResponseError"
        self.expected_details = "Status code: 401\nUnauthorized request."
        self.expected_status_code = self.exc.status_code

        self.execute_assert_raises()


class TestSetupDatabaseClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.database_id = "mock_database_id"

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    @patch("modules.connection_setup.CosmosClient")
    def execute_assert_raises(self, mock_cosmos_client) -> None:
        """Helper function to execute the assertRaises block."""

        expected_exception = QueryCosmosDBError
        mock_client = MagicMock()
        mock_client.get_database_client.side_effect = self.exc
        mock_cosmos_client.return_value = mock_client

        with self.assertRaises(expected_exception=expected_exception) as cm:
            setup_database_client(client=mock_client, database_id=self.database_id)

            self.assertEqual(
                first=cm.exception.status_code, second=self.expected_status_code
            )
            self.assertEqual(
                first=cm.exception.message,
                second=self.expected_message,
            )
            self.assertEqual(
                first=cm.exception.exception_type, second=self.expected_exception_type
            )
            self.assertEqual(first=cm.exception.details, second=self.expected_details)

    @patch("modules.connection_setup.CosmosClient")
    def test_successful_connection(self, mock_cosmos_client) -> None:
        """Test the function with a successful connection."""

        mock_database = MagicMock()
        mock_client = MagicMock()
        mock_client.get_database_client.return_value = mock_database
        mock_cosmos_client.return_value = mock_client

        result = setup_database_client(client=mock_client, database_id=self.database_id)

        self.assertEqual(first=result, second=mock_database)

    def test_invalid_database_id(self) -> None:
        """Test the function with an invalid database ID."""

        self.exc = cosmos_exc.CosmosResourceNotFoundError(message="Database not found.")
        self.expected_message = "CosmosDB database invalid_database_id was not found."
        self.expected_exception_type = "CosmosResourceNotFoundError"
        self.expected_details = "Status code: 0\nDatabase not found."
        self.expected_status_code = self.exc.status_code

        self.execute_assert_raises()

    def test_request_timeout(self) -> None:
        """Test the function with a request timeout."""

        self.exc = cosmos_exc.CosmosClientTimeoutError()
        self.expected_message = "Request timeout."
        self.expected_exception_type = "CosmosClientTimeoutError"
        self.expected_details = (
            "Client operation failed to complete within specified timeout."
        )
        self.expected_status_code = http_client.REQUEST_TIMEOUT

        self.execute_assert_raises()


class TestSetupContainerClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    @patch("modules.connection_setup.DatabaseProxy")
    def execute_assert_raises(self, mock_database_proxy) -> None:
        """Helper function to execute the assertRaises block."""

        expected_exception = QueryCosmosDBError
        container_id = "mock_container_id"
        mock_database = MagicMock()
        mock_database.get_container_client.side_effect = self.exc
        mock_database_proxy.return_value = mock_database

        with self.assertRaises(expected_exception=expected_exception) as cm:
            setup_container_client(
                database=mock_database,
                container_id=container_id,
            )

            self.assertEqual(
                first=cm.exception.status_code,
                second=self.expected_status_code,
            )
            self.assertEqual(
                first=cm.exception.message,
                second=self.expected_message,
            )
            self.assertEqual(
                first=cm.exception.exception_type,
                second=self.expected_exception_type,
            )
            self.assertEqual(
                first=cm.exception.details,
                second=self.expected_details,
            )

    @patch("modules.connection_setup.DatabaseProxy")
    def test_successful_connection(self, mock_database_proxy) -> None:
        """Test the function with a successful connection."""

        container_id = "mock_container_id"
        mock_container = MagicMock()
        mock_database = MagicMock()
        mock_database_proxy.return_value = mock_database
        mock_database.get_container_client.return_value = mock_container

        test_result = setup_container_client(
            database=mock_database, container_id=container_id
        )

        self.assertEqual(first=mock_container, second=test_result)

    def test_invalid_database_id(self) -> None:
        """Test the function with an invalid database ID."""

        self.exc = cosmos_exc.CosmosResourceNotFoundError(
            message="Container not found."
        )
        self.expected_message = "CosmosDB container mock_container_id was not found."
        self.expected_exception_type = "CosmosResourceNotFoundError"
        self.expected_details = "Status code: 0\nContainer not found."
        self.expected_status_code = self.exc.status_code

        self.execute_assert_raises()

    def test_request_timeout(self) -> None:
        """Test the function with a request timeout."""

        self.exc = cosmos_exc.CosmosClientTimeoutError()
        self.expected_message = "Request timeout."
        self.expected_exception_type = "CosmosClientTimeoutError"
        self.expected_details = (
            "Client operation failed to complete within specified timeout."
        )
        self.expected_status_code = http_client

        self.execute_assert_raises()


class TestMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    @patch("modules.connection_setup.setup_cosmos_client")
    @patch("modules.connection_setup.setup_database_client")
    @patch("modules.connection_setup.setup_container_client")
    @patch("modules.connection_setup.log")
    def test_valid_input(
        self,
        mock_logger,
        setup_container_client,
        setup_database_client,
        setup_cosmos_client,
    ) -> None:
        """Test the function with valid input."""

        connection_string = "mock_connection_string"
        database_id = "mock_database_id"
        container_id = "mock_container_id"

        mock_container_proxy = MagicMock(spec=ContainerProxy)

        mock_logger.info.return_value = None
        setup_cosmos_client.return_value = MagicMock()
        setup_database_client.return_value = MagicMock()
        setup_container_client.return_value = mock_container_proxy

        expected_result = mock_container_proxy

        test_result = main(
            connection_string=connection_string,
            database_id=database_id,
            container_id=container_id,
        )

        self.assertEqual(first=test_result, second=expected_result)

    def test_with_invalid_input(self) -> None:
        """There's no test to be done. Main function is a wrapper for other functions.
        Invalid input into the module will be handled by try/except blocks in called functions.
        """
        self.assertTrue(expr=True)


if __name__ == "__main__":
    unittest.main()
