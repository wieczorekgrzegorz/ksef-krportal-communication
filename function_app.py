"""HTTP trigger function to query CosmosDB database."""

# imports
import http.client as http_client
import logging
import os
import sys

# 3rd party imports
import azure.functions as func

# local imports
from modules.connection_setup import main as setup_cosmosdb_connection
from modules.get_query_from_body import main as get_query_from_body
from modules.query_cosmosDB import main as query_cosmosDB
from modules.utilities.exception_handler import handle_exception
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError

from modules.utilities.setup_logger import setup_logger

# # setup logging
log: logging.Logger = logging.getLogger(name="logging." + __name__)
setup_logger(level=logging.INFO)


# declare environment constants
CONNECTION_STRING: str = os.environ["AZURE_COSMOSDB_CONNECTION_STRING"]
DATABASE_ID: str = os.environ["DATABASE_ID"]
CONTAINER_ID: str = os.environ["CONTAINER_ID"]


# declare default HTTP response variables
DEFAULT_STATUS_CODE: int = http_client.INTERNAL_SERVER_ERROR
DEFAULT_BODY: str = "Unexpected error inside function query_cosmosDB, please contact function administrator."
HEADERS: dict[str, str] = {"Content-Type": "application/json"}


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name(name="query_cosmosDB")
@app.route(route="querycosmosdb", methods=["POST"])
def main(
    req: func.HttpRequest,
) -> func.HttpResponse:
    """
    HTTP trigger function to query CosmosDB database.

    Parameters:
        req (func.HttpRequest):
            HTTP request sent to Azure Function's endpoint.

    Attributes:

    Global variables:
        CONNECTION_STRING (str, constant):
            CosmosDB connection string. Environment variable. Default: os.environ["AZURE_COSMOSDB_CONNECTION_STRING"].
        DATABASE_ID (str, constant):
            CosmosDB database ID. Environment variable. Default: os.environ["CONTAINER_ID"].
        CONTAINER_ID (str, constant):
            CosmosDB container ID. Environment variable. Default: os.environ["CONTAINER_ID"].

        BODY (str, constant):
            HTTP response body. Default: Custom error message. Replaced with SQL query items in case of success,\
            or with error details in case of error.
        DEFAULT_STATUS_CODE (int, constant):
            HTTP response status code for internal server error. Default: 500.
        HEADERS (dict[str, str], optional constant):
            HTTP response headers. Constant. Default: {"Content-Type": "application/json"}.

    Returns:
        func.HttpResponse: HTTP response in format: {
            body (str): query items in JSON format, or error details in case of error. JSON format:
                {id (str): query items (dict: str, str)}
            headers (dict[str, str]): "Content-Type": "application/json",
            status_code (int): Depends on the outcome of the function.
            }

    Raises:
        none - all exceptions are handled by handle_exception() function in order to return\
            HTTP response with error details in body and status code fitting the exception.

    Usage instruction:
        To use the query_cosmosDB function, you need to provide a JSON payload in the body of the HTTP request.
        The payload should contain the following fields:
            query:
                The SQL query to execute. Warning: call SELECT must contain id in unchanged form for the app to work
                (e.g. SELECT c.id, c.NIP FROM c is allowed, SELECT c.id as 'not_id' FROM c is not allowed).
        Example payload:
            {
                "query": "SELECT c.id, c.NIP FROM c"
            }
        Query's result is returned in response's body in json format, with status code 200.

        In case of error, response's body contains error details and status code fitting the error.

    WARNING:
        Do not change the name of "id" column in SQL query ("SELECT c.id as 'not_id' FROM c" is not allowed)\
        as it is used to build the dictionary of query items in function query_cosmosDB.list_to_dict().
    """
    # if try/except block fails to handle exception, default HTTP response is returned
    body = DEFAULT_BODY
    status_code = DEFAULT_STATUS_CODE
    try:
        log.info(msg="Query_CosmosDB received a request.")

        sql_query = get_query_from_body(req=req)

        container = setup_cosmosdb_connection(
            connection_string=CONNECTION_STRING,
            database_id=DATABASE_ID,
            container_id=CONTAINER_ID,
        )

        body, status_code = query_cosmosDB(container=container, sql_query=sql_query)

        log.info(msg="Query_CosmosDB retrieved items from CosmosDB successfully.")

    except QueryCosmosDBError as exc:
        exc_type, exc_value, exc_traceback = sys.exc_info()  # pylint: disable=W0612
        body, status_code = handle_exception(exc=exc)

    except Exception:  # pylint: disable=W0718
        # if unhandled exception, return default HTTP response with error details and use default status code (500)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        body = {"exception": exc_type.__name__, "message": exc_value}  # type: ignore
        # "except Exceptions" is enough to know there is an exception with a name and a value

    finally:
        log.info(
            msg=f"Query_CosmosDB returned HTTP response with status code {status_code}."
        )
        return func.HttpResponse(  # pylint: disable=W0150 # "finally" block always returns a value
            body=str(object=body),
            headers=HEADERS,
            status_code=status_code,
        )
