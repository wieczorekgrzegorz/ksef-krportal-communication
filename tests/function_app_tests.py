import http.client as http_client
import json
import unittest
from unittest.mock import MagicMock, patch

import azure.functions as func
from azure.cosmos import ContainerProxy

import context  # noqa: F401 # context imported for mocking environment variables and inserting PATH
import function_app

# turn off logs for testing
context.turn_off_logging(module="function_app")


class TestFunctionApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        print(f"\n### STARTING TEST: {cls.__name__} ###")
        cls.maxDiff = None
        cls.request_url: str = "mock_url"
        cls.request_method: str = "POST"
        cls.request_body_string: str = "SELECT * FROM c"
        cls.request_headers: dict[str, str] = {"Content-Type": "application/json"}
        cls.request = func.HttpRequest(
            method=cls.request_method,
            url=cls.request_url,
            headers=cls.request_headers,
            body=cls.request_body_string.encode(encoding="utf-8"),
        )

    @classmethod
    def tearDownClass(cls) -> None:
        patch.stopall()
        print(f"\n### FINISHED TEST: {cls.__name__} ###\n")

    def test_function_app_getting_environmental_variables(self) -> None:
        """Tests function_app getting environmental variables.
        For unit testing, environmental variables are mocked in context.py."""
        mock_connection_string = context.os.environ["AZURE_COSMOSDB_CONNECTION_STRING"]
        mock_database_id = context.os.environ["DATABASE_ID"]
        mock_container_id = context.os.environ["CONTAINER_ID"]

        self.assertEqual(
            first=function_app.CONNECTION_STRING, second=mock_connection_string
        )
        self.assertEqual(first=function_app.DATABASE_ID, second=mock_database_id)
        self.assertEqual(first=function_app.CONTAINER_ID, second=mock_container_id)

    @patch("function_app.get_query_from_body")
    @patch("function_app.setup_cosmosdb_connection")
    @patch("function_app.query_cosmosDB")
    def test_with_valid_input(
        self, query_cosmosDB, setup_cosmosdb_connection, get_query_from_body
    ) -> None:
        """Tests function_app with valid input."""
        mock_query_body: str = "mock_query_body"
        mock_response_status_code: int = http_client.OK
        get_query_from_body.return_value = self.request_body_string
        setup_cosmosdb_connection.return_value = MagicMock(spec=ContainerProxy)
        query_cosmosDB.return_value = (
            mock_query_body,
            mock_response_status_code,
        )

        expected_response = func.HttpResponse(
            body=mock_query_body,
            status_code=mock_response_status_code,
            headers=self.request_headers,
        )

        func_call = function_app.main.build().get_user_function()
        actual_response = func_call(self.request)

        self.assertEqual(
            first=actual_response.__dict__, second=expected_response.__dict__
        )

    @patch("function_app.get_query_from_body")
    @patch("function_app.setup_cosmosdb_connection")
    @patch("function_app.query_cosmosDB")
    def test_with_QueryCosmosDBError(
        self, query_cosmosDB, setup_cosmosdb_connection, get_query_from_body
    ) -> None:
        """Tests function_app with QueryCosmosDBError exception raised by one of the functions called inside main.
        QueryCosmosDBError should be handled by exception_handler, and thus the app should return http response with
        status code and body from QueryCosmosDBError.
        QueryCosmosDBError is raised by query_cosmosDB function."""
        exception_type: str = "mock exception type"
        message: str = "mock error message"
        status_code: int = http_client.NOT_FOUND
        details: str = "mock details"

        expected_query_body: bytes = json.dumps(
            obj={
                "exception": exception_type,
                "message": message,
                "status_code": status_code,
                "details": details,
            },
            indent=4,
            sort_keys=False,
            ensure_ascii=False,
        ).encode(encoding="utf-8")

        get_query_from_body.return_value = self.request_body_string
        setup_cosmosdb_connection.return_value = MagicMock(spec=ContainerProxy)
        query_cosmosDB.side_effect = function_app.QueryCosmosDBError(
            exception_type=exception_type,
            message=message,
            status_code=status_code,
            details=details,
        )

        req = self.request

        expected_response = func.HttpResponse(
            body=expected_query_body,
            status_code=status_code,
            headers=self.request_headers,
        )

        func_call = function_app.main.build().get_user_function()
        actual_response = func_call(req)

        self.assertEqual(
            first=actual_response.__dict__, second=expected_response.__dict__
        )

    @patch("function_app.get_query_from_body")
    @patch("function_app.setup_cosmosdb_connection")
    @patch("function_app.query_cosmosDB")
    def test_with_unknown_Exception(
        self, query_cosmosDB, setup_cosmosdb_connection, get_query_from_body
    ) -> None:
        """
        Tests function_app with an exception other than QueryCosmosDBError raised by one of the functions called inside main.
        Exceptions other than QueryCosmosDBError are not handled by exception_handler, and thus the app should return http response with http_client.INTERNAL_SERVER_ERROR as status code and Exceptions message as body.
        Exception ValueError("mock exception") is raised by query_cosmosDB function."""
        test_exception = ValueError("mock exception")
        test_exception_type = test_exception.__class__.__name__

        expected_query_body = str(
            object={
                "exception": test_exception_type,
                "message": test_exception,
            }
        ).encode(encoding="utf-8")

        mock_response_status_code: int = http_client.INTERNAL_SERVER_ERROR
        get_query_from_body.return_value = self.request_body_string
        setup_cosmosdb_connection.return_value = MagicMock(spec=ContainerProxy)
        query_cosmosDB.side_effect = test_exception

        req = self.request

        expected_response = func.HttpResponse(
            body=expected_query_body,
            status_code=mock_response_status_code,
            headers=self.request_headers,
        ).__dict__

        func_call = function_app.main.build().get_user_function()
        actual_response = func_call(req)

        self.assertEqual(first=actual_response.__dict__, second=expected_response)


if __name__ == "__main__":
    unittest.main()
