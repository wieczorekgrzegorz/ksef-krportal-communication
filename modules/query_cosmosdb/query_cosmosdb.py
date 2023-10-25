"""Facilitates process of querying CosmosDB container."""
import http.client as http_client
import logging
import sys
from typing import Callable

import azure.functions as func

from .modules import get_query_from_body, get_query_items, connection_setup
from .modules.custom_error import QueryCosmosDBError


log = logging.getLogger(name="log." + __name__)


def main(  # pylint: disable=R0913
    req: func.HttpRequest,
    cosmosdb_connection_string: str,
    cosmosdb_database_id: str,
    cosmosdb_container_id: str,
    exception_handler: Callable,
    default_body: str = "Unexpected error, please contact function administrator.",
    default_status_code: int = http_client.INTERNAL_SERVER_ERROR,
) -> tuple[str, int]:
    """
    Queries CosmosDB container with an SQL query provided in HTTP request's body and returns query items in json format.

    Parameters:
        req (func.HttpRequest): HTTP request sent to Azure Function's endpoint.
        cosmosdb_connection_string (str): CosmosDB connection string.
        cosmosdb_database_id (str): CosmosDB database ID (name).
        cosmosdb_container_id (str): CosmosDB container ID (name).
        default_body (str, optional): Default message, changed in course of execution od the function.
        default_status_code (int, optional): HTTP status code OK (200). Default value, 200, is returned unchanged\
            if no exception encountered.

    Returns:
        tuple (str,int):
            query_items (str):
                query items (invoices) in a JSON string: {"id_1": {json_1}, "id_2": {json_2}, {...}, "id_n": {json_n}},
                if SQL query returned any items. If not, a default message "Query returned no items." is returned.
            status_code (int):
                HTTP status code OK (200).

    Raises:
        QueryCosmosDBError:
            If failed to get request's body or request's body was found to be empty (in get_query_from_body).
            If failed to connect with host declared in AccountEndpoint (in setup_cosmos_client).
            If CosmosDB host URL is invalid (in setup_cosmos_client).
            If request times out (in setup_cosmos_client).
            If input authorization token can't serve the request (in setup_cosmos_client).
            If database is not found (in setup_cosmos_client).
            If CosmosDB container is not found (in get_query_items).
            If request times out (in get_query_items).
            If query fails to run (in get_query_items).
            If key 'id' not found in iterable. (in get_query_items)
            If upon iterating through first item in iterable, it is found to carry an information on failed query.\
                (in get_query_items)
            If failed to convert query items dictionary to JSON string (in get_query_items).
    """
    status_code = default_status_code
    body = default_body

    try:
        sql_query = get_query_from_body.main(req=req)

        container = connection_setup.main(
            connection_string=cosmosdb_connection_string,
            database_id=cosmosdb_database_id,
            container_id=cosmosdb_container_id,
        )

        body = get_query_items.main(container=container, sql_query=sql_query)
        status_code = http_client.OK

    except QueryCosmosDBError as exc:
        body, status_code = exception_handler(exc=exc)

    except Exception:  # pylint: disable=W0718
        # if unhandled exception, return default HTTP response with error details and use default status code (500)
        exc_type, exc_value, exc_traceback = sys.exc_info()  # pylint: disable=W0612
        body = str(object={"exception": exc_type.__name__, "message": exc_value})  # type: ignore
        status_code = http_client.INTERNAL_SERVER_ERROR
        # "except Exceptions" is enough to know there is an exception with a name and a value

    return body, status_code
