"""Facilitates process of querying CosmosDB container."""
from collections.abc import Iterable
import http.client as http_client
import json
import logging

from typing import Any


from azure.cosmos import exceptions as cosmos_exceptions
from azure.cosmos import ContainerProxy

from .utilities.query_cosmosDB_error import QueryCosmosDBError


log = logging.getLogger(name="log." + __name__)


def get_query_items(
    container: ContainerProxy, sql_query: str
) -> Iterable[dict[str, Any]]:
    """
    Requests CosmosDB container with an SQL query provided in HTTP request's body and returns query items.

    Parameters:
        container (ContainerProxy): CosmosDB container client.
        query (str): Query string obtained from get_requests_body().

    Returns:
        query_items (Iterable[dict[str, Any]]): iterable object containing query items (invoices) as returned by CosmosDB.

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
            status_code=exc.status_code,
        )

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
            status_code=exc.status_code,
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
            If upon iterating through first item in iterable, it is found to carry an information on failed query. (cosmos_exceptions.CosmosHttpResponseError)
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
                    details=None,
                    message=custom_message,
                    status_code=http_client.BAD_REQUEST,
                ) from exc

    except cosmos_exceptions.CosmosHttpResponseError as exc:
        custom_message = "HTTP Response Error. Check details for more information."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=exc.status_code,
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
            details=None,
            message=custom_message,
            status_code=http_client.INTERNAL_SERVER_ERROR,
        ) from exc

    log.debug(msg="Query items dictionary converted to JSON string succesfully.")
    return query_items_json


def main(
    container: ContainerProxy,
    sql_query: str,
    status_code: int = http_client.OK,
    query_items: str = "Query returned no items.",
) -> tuple[str, int]:
    """
    Queries CosmosDB container with an SQL query provided in HTTP request's body and returns query items in json format.\n

    Parameters:
        container (azure.cosmos.ContainerProxy):
            A ContainerProxy instance representing the retrieved database.
        query (str):
            SQL Query string in string format.
        status_code (int, optional):
            HTTP status code OK (200). Default value, 200, is returned unchanged if no exception encountered.
        query_items (str, optional):
            Default message "Query returned no items.", overwritten if query returns any items.

    Returns:
        query_items (str):
            query items (invoices) in a JSON string: {"id_1": {json_1}, "id_2": {json_2}, {...}, "id_n": {json_n}}, if
            SQL query returned any items. If not, a default message "Query returned no items." is returned.
        status_code (int):
            HTTP status code OK (200).

    Raises:
        QueryCosmosDBError:
            If CosmosDB container is not found.
                in function: get_query_items;
                from exception: cosmos_exceptions.CosmosResourceNotFoundError;
            If request times out.
                in function: get_query_items;
                from exception: cosmos_exceptions.CosmosClientTimeoutError;
            If query fails to run (get_query_items, cosmos_exceptions.CosmosHttpResponseError).
                in function: get_query_items;
                from exception: cosmos_exceptions.CosmosHttpResponseError;
            If key 'id' not found in iterable.
                in function iterable_to_dict;
                from exception: KeyError;
            If upon iterating through first item in iterable, it is found to carry an information on failed query. in function iterable_to_dict;
                from exception: cosmos_exceptions.CosmosHttpResponseError;
            If failed to convert query items dictionary to JSON string (TypeError).
                in function: dict_to_json;
                from exception: TypeError;


    HOW IT WORKS:\n
        Step 1. get_query_items sends an SQL query to CosmosDB container. and receives query items (invoices) list as returned by CosmosDB: [{json_1}, {json_2}, {...}, {json_n}]. The list is saved to query_items_list.\n
        Step 2. list_to_dict converts list of invoices to dictionary following the pattern: {ksef_id: invoice_content}. WATCHOUT: for it ro works, query sent to CosmosDB can't rename column 'id' to anything else.\n
        Step 3. dict_to_json converts dictionary of invoices to JSON string: {"id_1": {json_1}, "id_2": {json_2}, {...}, "id_n": {json_n}}. JSON string is saved to query_items_json.\n
        Step 4. query_items_json is returned as string.\n
    """

    query_items_raw = get_query_items(container=container, sql_query=sql_query)

    query_items_dict = iterable_to_dict(iterable=query_items_raw)

    if query_items_dict == {}:
        # If query returned no items, return default query_items and status code 200.
        # can't use http_client.NO_CONTENT (=204) as it is not allowed to return body with 204
        log.info(msg=query_items)
        return query_items, status_code

    query_items = dict_to_json(query_items_dict=query_items_dict)

    log.info(msg="Query items converted to JSON string succesfully.")
    return query_items, status_code
