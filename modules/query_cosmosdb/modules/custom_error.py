"""Custom exception class for for handling common errors in query_cosmosDB."""

import json
import logging
from typing import Optional


log = logging.getLogger(name="log." + __name__)


class QueryCosmosDBError(Exception):
    """
    Custom exception class for for handling common errors in query_cosmosDB.

    Collects error details from the exception info tuple and builds error_response following the format:
        {
            "exception": exception_type,
            "message": message,
            "status_code": status_code,
            "details": details,
        },
    to be returned as HTTP response body.

    Parameters:
        exception_type (str): Exception type.
        details (Optional[str]): Exception details.
        message (Optional[str]): Custom exception message.
        status_code (Optional[int]): HTTP status code.

    Attributes:
        exception_type (str): Exception type.
        details (Optional[str]): Exception details.
        message (Optional[str]): Custom exception message.
        status_code (Optional[int]): HTTP status code.
        error_response (str): JSON string representing error_response_dict.

    Raises:
        Exception: If failed to build error_response.

    Examples:
        try:
            raise ValueError("This is a ValueError.")
        except ValueError as exc:
            custom_message = "Example custom message."
            raise QueryCosmosDBError(
                exception_type=exc.__class__.__name__,
                details=exc.message,
                message=custom_message,
                status_code=http_client.INTERNAL_SERVER_ERROR,
        )
    """

    exception_type: str
    details: str
    message: str
    status_code: int

    def __init__(
        self,
        exception_type: str,
        details: str,
        message: str,
        status_code: int,
    ) -> None:
        self.exception_type = exception_type
        self.details = details
        self.message = message
        self.status_code = status_code

        error_response_dict = self.build_error_response()
        self.error_response = self.convert_to_json(
            error_response_dict=error_response_dict
        )

    def __str__(self) -> str:
        return f"QueryCosmosDBError for passed {self.exception_type} exception"

    def build_error_response(self) -> dict[str, Optional[str] | Optional[int]]:
        """
        Builds error_response from exception info following the format:
            {
                "exception" (str): exception_type,
                "message" (Optional[str]): message,
                "status_code" (Optional[int]): status_code,
                "details" (Optional[str]): details,
            }
        """
        return {
            "exception": self.exception_type,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }

    def convert_to_json(self, error_response_dict) -> str:
        """
        Converts error_response_dict to JSON string. Provides fallback in case of TypeError.

        Returns:
            error_response (str):
                JSON string representing error_response_dict. In case of error, returns string representation\
                of error_response_dict (without JSON formatting).
        """
        try:
            error_response = json.dumps(
                obj=error_response_dict, indent=4, sort_keys=False, ensure_ascii=False
            )

        except TypeError:
            try:
                for key, value in error_response_dict.items():
                    error_response_dict[key] = str(object=value)

                error_response = json.dumps(
                    obj=error_response_dict,
                    indent=4,
                    sort_keys=False,
                    ensure_ascii=False,
                )

            except Exception:  # pylint: disable=W0718
                # catching general exception is intentional here
                # I can't think of a scenario where this would happen, but just in case.
                log.warning(
                    msg=f"Failed to convert error_response_dict to JSON after converting values to string.\
                        error_response_dict: {error_response_dict}"
                )
                error_response = str(object=error_response_dict)

        return error_response
