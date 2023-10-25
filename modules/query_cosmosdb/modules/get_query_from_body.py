"""Facilitates process of querying CosmosDB container."""
import http.client as http_client
import logging
import sys

import azure.functions as func

from .custom_error import QueryCosmosDBError


log = logging.getLogger(name="log." + __name__)


def get_json_from_payload(payload: func.HttpRequest) -> dict:
    """
    Gets JSON payload from HTTP request's body.

    Parameters:
        payload (func.HttpRequest):
            HTTP request sent to Azure Function's endpoint.

    Returns:
        json_payload (dict):
            JSON payload retrieved from HTTP request's body.

    Raises:
        QueryCosmosDBError:
            If failed to get request's body or request's body was found to be empty. (ValueError)
    """
    try:
        json_payload = payload.get_json()
    except ValueError as exc:
        custom_message = "Failed to get request's body or request's body is empty."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=str(object=sys.exc_info()),
            message=custom_message,
            status_code=http_client.BAD_REQUEST,
        ) from exc

    return json_payload


def get_query_from_payload(json_payload: dict) -> str:
    """
    Extracts the value of the 'query' field from an HTTP request payload.

    Parameters:
        payload (Dict): The HTTP request payload as a dictionary.

    Returns:
        str: The value of the 'query' field.

    Raises:
        KeyError: If the 'query' field is not present in the payload.
    """
    try:
        query = json_payload["query"]
    except KeyError as exc:
        custom_message = "Request's body missing 'query' field."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=str(object=sys.exc_info()),
            message=custom_message,
            status_code=http_client.BAD_REQUEST,
        ) from exc
    return query


def main(req: func.HttpRequest) -> str:
    """
    Retrieves an SQL query provided in HTTP request's body.\n:

    Parameters:
        req (HttpRequest):
            HTTP request sent to Azure Function's endpoint.

    Returns:
        sql_query (str):
            SQL query string in string format.

    Raises:
        QueryCosmosDBError:
            If failed to get request's body or request's body was found to be empty.
                in function: get_requests_body;
                from exception: ValueError.
            If request's body cannot be decoded in UTF-8.
                in function: decode_body;
                from exception: UnicodeDecodeError.
    """
    json_payload = get_json_from_payload(payload=req)

    sql_query = get_query_from_payload(json_payload=json_payload)

    log.info(msg="HTTP requests processed succesfully.")
    return sql_query
