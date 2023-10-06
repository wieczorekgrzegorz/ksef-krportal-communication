# flake8: noqa: F401, F402 # tests from test modules are called by unittest.main()

import unittest

import context
from connection_setup_tests import (
    TestSetupCosmosClient,
    TestSetupDatabaseClient,
    TestSetupContainerClient,
    TestMain,
)
from exception_handler_tests import TestHandleException
from function_app_tests import TestFunctionApp
from query_cosmosDB_tests import (
    TestIterableToDict,
    TestDictToJson,
    TestGetQueryItems,
    TestMain,
)
from get_query_from_body_tests import TestGetRequestsBody, TestMain
from query_cosmosDB_error_tests import TestQueryCosmosDBError

if __name__ == "__main__":
    # turn off logs for testing
    context.turn_off_logging(module="modules.get_query_from_body")
    context.turn_off_logging(module="modules.utilities.exception_handler")

    unittest.main()
