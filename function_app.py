"""HTTP trigger function to query CosmosDB database."""

# imports
import http.client as http_client
import logging
import os
import sys

# 3rd party imports
import azure.functions as func
from azure.storage.blob import BlobServiceClient


# local imports
from modules import connection_setup
from modules import get_query_from_body
from modules import query_cosmosDB
from modules.utilities.exception_handler import handle_exception
from modules.utilities.query_cosmosDB_error import QueryCosmosDBError

from modules.utilities.setup_logger import setup_logger

# # setup logging
log: logging.Logger = logging.getLogger(name="logging." + __name__)
setup_logger(level=logging.INFO)


# declare environment constants
CONNECTION_STRING: str = os.environ["COSMOSDB_CONNECTION_STRING"]
DATABASE_ID: str = os.environ["COSMOSDB_DATABASE_ID"]
CONTAINER_ID: str = os.environ["COSMOSDB_CONTAINER_ID"]
BLOB_SERVICE_CONNECTION_STRING: str = os.environ["BLOB_CONNECTION_STRING"]
BLOB_CONTAINER_NAME: str = os.environ["BLOB_CONTAINER_NAME"]


# declare default HTTP response variables
DEFAULT_STATUS_CODE: int = http_client.INTERNAL_SERVER_ERROR
DEFAULT_BODY: str = "Unexpected error inside function query_cosmosDB, please contact function administrator."
HEADERS: dict[str, str] = {"Content-Type": "application/json"}


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.function_name(name="download_BLOB")
@app.route(route="downloadblob", methods=["POST", "GET"])
def downloadblob_app(
    req: func.HttpRequest,
) -> func.HttpResponse:
    """
    _summary_

    Args:
        req (func.HttpRequest): _description_

    Returns:
        func.HttpResponse: _description_
    """
    HEADERS: dict[str, str] = {"Content-Type": "application/xml"}

    invoice_id = req.params.get("invoice_id")

    if invoice_id is None:
        return func.HttpResponse(
            body=b"Please provide invoice_id parameter in the request.",
            status_code=http_client.BAD_REQUEST,
        )

    if req.params.get("single_file_download") == "true":
        blob_name = req.params.get("invoice_id") + ".xml"  # type: ignore # invoice_id is None is checked before

        client = BlobServiceClient.from_connection_string(
            conn_str=BLOB_SERVICE_CONNECTION_STRING
        )
        container_client = client.get_container_client(container=BLOB_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(blob=blob_name)

        blob = blob_client.download_blob()
        invoice = blob.readall()

        print(f"Blob downloaded: {blob_name}")
        print(f"Blob content: {invoice}")
        return func.HttpResponse(body=invoice, status_code=200, headers=HEADERS)

    return func.HttpResponse(
        body=b"Package download not implemented yet.", status_code=200
    )


@app.function_name(name="query_cosmosDB")
@app.route(route="querycosmosdb", methods=["POST"])
def querycosmosdb_app(
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

        sql_query = get_query_from_body.main(req=req)

        container = connection_setup.main(
            connection_string=CONNECTION_STRING,
            database_id=DATABASE_ID,
            container_id=CONTAINER_ID,
        )

        body, status_code = query_cosmosDB.main(
            container=container, sql_query=sql_query
        )

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
        return func.HttpResponse(  # pylint: disable=return-in-finally, lost-exception
            # "overshadowing" is an expected behaviour in this case
            body=str(object=body),
            headers=HEADERS,
            status_code=status_code,
        )
