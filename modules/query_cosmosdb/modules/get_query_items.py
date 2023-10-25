"""Module containing functions for querying CosmosDB container with an SQL query provided in HTTP request's body
and returning query items in json format."""

from collections.abc import Iterable
import http.client as http_client
import json
import logging
import sys
from typing import Any

from azure.cosmos import exceptions as cosmos_exceptions
from azure.cosmos import ContainerProxy

from .custom_error import QueryCosmosDBError


log = logging.getLogger(name="log.query_cosmosdb." + __name__)


def get_query_items(
    container: ContainerProxy, sql_query: str
) -> Iterable[dict[str, Any]]:
    """
    Requests CosmosDB container with an SQL query provided in HTTP request's body and returns query items.

    Parameters:
        container (ContainerProxy): CosmosDB container client.
        query (str): Query string obtained from get_requests_body().

    Returns:
        query_items (Iterable[dict[str, Any]]): object containing query items (invoices) as returned by CosmosDB.

    Raises:
        QueryCosmosDBError:
            If CosmosDB container is not found (cosmos_exceptions.CosmosResourceNotFoundError).
            If request times out (cosmos_exceptions.CosmosClientTimeoutError).
            If query fails to run (cosmos_exceptions.CosmosHttpResponseError).
    """
    log.debug(msg="Querying CosmosDB container.")

    try:
        query_items = container.query_items(
            query=sql_query,
            enable_cross_partition_query=True,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/query+json",
                "x-ms-documentdb-query-enablecrosspartition": "True",
                "x-ms-documentdb-isquery": "True",
            },
        )

    except cosmos_exceptions.CosmosResourceNotFoundError as exc:
        custom_message = "CosmosDB resource not found. Check connection string."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=exc.status_code,  # type: ignore
        ) from exc

    except cosmos_exceptions.CosmosClientTimeoutError as exc:
        custom_message = "Request timeout."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=http_client.REQUEST_TIMEOUT,
        ) from exc

    except cosmos_exceptions.CosmosHttpResponseError as exc:
        custom_message = "HTTP Response Error. Please check details."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=exc.status_code,  # type: ignore
        ) from exc

    log.debug(msg="CosmosDB container queried succesfully.")
    return query_items


def iterable_to_dict(iterable: Iterable[dict[str, Any]]) -> dict:
    """
    Converts ItemPaged object to dictionary following the pattern: {ksef_id: invoice_content}.

    Parameters:
        iterable (Iterable[dict[str, Any]]): Iterable object to convert to dictionary.

    Returns:
        query_items_dict (dict): Dictionary of query items in format:
            {id: {query items}.

    Raises:
        QueryCosmosDBError:
            If key 'id' not found in iterable. (KeyError)
            If upon iterating through first item in iterable, it is found to carry an information on failed query.\
                (cosmos_exceptions.CosmosHttpResponseError)
    """
    log.debug(msg="Converting query items to dictionary.")

    query_items_dict = {}
    try:
        for item in iterable:
            try:
                query_items_dict[item["id"]] = item
            except KeyError as exc:
                custom_message = f"Key 'id' not found in {item}. Perhaps your query renamed column 'id'?"
                raise QueryCosmosDBError(
                    exception_type=exc.__class__.__name__,
                    details=str(object=sys.exc_info()),
                    message=custom_message,
                    status_code=http_client.BAD_REQUEST,
                ) from exc

    except cosmos_exceptions.CosmosHttpResponseError as exc:
        custom_message = "HTTP Response Error. Check details for more information."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=exc.status_code,  # type: ignore
        ) from exc

    log.debug(msg="Query items converted to dictionary succesfully.")
    return query_items_dict


def dict_to_json(query_items_dict: dict) -> str:
    """
    Converts dictionary of invoices to JSON string.

    Parameters:
        query_items_dict (dict): Dictionary of query query_items_list returned by list_to_dict().

    Returns:
        query_items_json (str): JSON string representing query_items_dict.

    Raises:
        QueryCosmosDBError:
            If failed to convert query items dictionary to JSON string (TypeError).
    """
    log.debug(msg="Converting query items dictionary to JSON string.")

    try:
        query_items_json = json.dumps(
            obj=query_items_dict, indent=4, sort_keys=False, ensure_ascii=False
        )
    except TypeError as exc:
        custom_message = "Failed to convert query items dictionary to JSON string."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=str(object=sys.exc_info()),
            message=custom_message,
            status_code=http_client.INTERNAL_SERVER_ERROR,
        ) from exc

    log.debug(msg="Query items dictionary converted to JSON string succesfully.")
    return query_items_json


def main(
    container: ContainerProxy,
    sql_query: str,
    default_query_items: str = "Query returned no items.",
) -> str:
    """
    Queries CosmosDB container with an SQL query provided in HTTP request's body and returns query items in json format.

    Args:
        container (azure.cosmos.ContainerProxy): a ContainerProxy instance representing the retrieved database.
        sql_query (str): SQL query string in string format.
        default_query_items (str, optional): default message to be returned if SQL query returned no items.\
            Defaults to "Query returned no items.".

    Returns:
        str: query items (invoices) in a JSON string: {"id_1": {json_1}, "id_2": {json_2}, {...}, "id_n": {json_n}}, if
            SQL query returned any items. If not, a default message "Query returned no items." is returned.

    Raises:
        QueryCosmosDBError:
            If CosmosDB container is not found (cosmos_exceptions.CosmosResourceNotFoundError).
            If request times out (cosmos_exceptions.CosmosClientTimeoutError).
            If query fails to run (cosmos_exceptions.CosmosHttpResponseError).
            If key 'id' not found in iterable. (KeyError)
            If upon iterating through first item in iterable, it is found to carry an information on failed query.\
                (cosmos_exceptions.CosmosHttpResponseError)
            If failed to convert query items dictionary to JSON string (TypeError).

    """
    query_items_raw = get_query_items(container=container, sql_query=sql_query)

    query_items_dict = iterable_to_dict(iterable=query_items_raw)

    if not query_items_dict:
        # If query returned no items, return default query_items and status code 200.
        # can't use http_client.NO_CONTENT (=204) as it is not allowed to return body with 204
        log.info(msg=default_query_items)
        return default_query_items

    query_items = dict_to_json(query_items_dict=query_items_dict)

    return query_items
