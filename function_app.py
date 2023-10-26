"""HTTP trigger function to query CosmosDB database."""

# imports
import logging

# 3rd party imports
import azure.functions as func

# local imports
from modules.query_cosmosdb import query_cosmosdb
from modules.download_blob import download_blob
from utilities import exception_handler, setup, parse_xsl

# # setup logging
log: logging.Logger = logging.getLogger(name="log." + __name__)
setup.logger(level=logging.DEBUG)

xlst_transformer = parse_xsl.transform_styl_xls_to_XLST(
    xsl_path="ksef_documents/styl.xsl"
)


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
    log.info(msg="download_BLOB received a request.")

    headers: dict[str, str] = {"Content-Type": "application/xml"}

    body, status_code = download_blob.main(
        req=req,
        blob_connection_string=setup.BLOB_SERVICE_CONNECTION_STRING,
        blob_container_name=setup.BLOB_CONTAINER_NAME,
        exception_handler=exception_handler.handle_cosmosdb_error,
        xslt_transformer=xlst_transformer,
    )

    log.info(
        msg=f"download_BLOB returned HTTP response with status code {status_code}."
    )
    return func.HttpResponse(
        body=body,
        headers=headers,
        status_code=status_code,
    )


@app.function_name(name="query_cosmosDB")
@app.route(route="querycosmosdb", methods=["POST"])
def querycosmosdb_app(
    req: func.HttpRequest,
) -> func.HttpResponse:
    """
    HTTP trigger function to query CosmosDB database.

    Parameters:
        req (func.HttpRequest): HTTP request sent to Azure Function's endpoint.

    Attributes:
        headers (dict[str, str], optional constant):
            HTTP response headers. Constant. Default: {"Content-Type": "application/json"}.

    Global variables:
        COSMOSDB_CONNECTION_STRING (str, constant):
            CosmosDB connection string. Environment variable. Default: os.environ["AZURE_COSMOSDB_CONNECTION_STRING"].
        COSMOSDB_DATABASE_ID (str, constant):
            CosmosDB database ID. Environment variable. Default: os.environ["CONTAINER_ID"].
        COSMOSDB_CONTAINER_ID (str, constant):
            CosmosDB container ID. Environment variable. Default: os.environ["CONTAINER_ID"].


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
    log.info(msg="Query_CosmosDB received a request.")

    headers: dict[str, str] = {"Content-Type": "application/json"}

    body, status_code = query_cosmosdb.main(
        req=req,
        cosmosdb_connection_string=setup.COSMOSDB_CONNECTION_STRING,
        cosmosdb_database_id=setup.COSMOSDB_DATABASE_ID,
        cosmosdb_container_id=setup.COSMOSDB_CONTAINER_ID,
        exception_handler=exception_handler.handle_cosmosdb_error,
    )

    log.info(
        msg=f"Query_CosmosDB returned HTTP response with status code {status_code}."
    )
    return func.HttpResponse(
        body=str(body),
        headers=headers,
        status_code=status_code,
    )
