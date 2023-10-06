"""Collects error details from the exception info tuple."""
import json
import logging
from http import HTTPStatus
import http.client as http_client

from .query_cosmosDB_error import QueryCosmosDBError

log = logging.getLogger(name="log." + __name__)


def handle_exception(
    exc: QueryCosmosDBError,
) -> tuple[str, HTTPStatus | int | None]:
    """
    Handles QueryCosmosDBError exceptions in order to allow query_cosmosDB to pass detailed information on encountered exception into HTTP response body.

    Parameters:
        exc (QueryCosmosDBError): QueryCosmosDBError exception.

    Returns:
        error_response (str): JSON string representing a dictionary of QueryCosmosDBError's attributes following the format:
            {
                "exception": exception_type,
                "message": message,
                "status_code": status_code,
                "details": details,
            },
        status_code (int): HTTP status code corresponding to the exception, as per common HTTP status codes.
    Raises:
        QueryCosmosDBError: If failed to find error_response or status_code in exc.
    """
    try:
        exception_type = exc.exception_type
        error_response = exc.error_response
        status_code = exc.status_code
        log.error(
            msg=f"Exception {exception_type} handled.\nReturned HTTP Response body: {error_response}"
        )

        return error_response, status_code
    except Exception as exception:
        # If failed to find error_response or status_code in exc.
        # I can't imagine how this could happen, but just in case.
        exception_type = exc.__class__.__name__
        status_code = http_client.INTERNAL_SERVER_ERROR
        message = "Unhandled exception. Please contact system administrator."
        details = None

        error_response_dict = {
            "exception": str(object=exception_type),
            "message": str(object=message),
            "status_code": str(object=status_code),
            "details": str(object=details),
        }
        error_response = json.dumps(
            obj=error_response_dict, indent=4, sort_keys=False, ensure_ascii=False
        )

        log.error(
            msg=f"couldn't find error_response or status_code in exc. Exception: {exception}"
        )
        return error_response, status_code
