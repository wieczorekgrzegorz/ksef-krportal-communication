"""Reads parameters of received http request"""
import http.client as http_client
import logging
from typing import Optional

import azure.functions as func

from .custom_error import DownloadBlobError

log = logging.getLogger(name="log." + __name__)


def main(req: func.HttpRequest, params_list: Optional[list] = None) -> dict[str, str]:
    """
    Reads parameters of received http request.

    Args:
        req (azure.functions.HttpRequest): HTTP request sent to Azure Function's endpoint.
        params_list (Optional[list], optional): list of parameters expected in the request.\
            Defaults to ["invoice_id", "single_file_download", "file_format"].

    Raises:
        DownloadBlobError: if any of the expected parameters is not found in the request.

    Returns:
        dict[str, str]: dictionary of parameters and their values.
    """
    log.debug(msg=f"Reading parameters of the request {req}.")
    if params_list is None:
        params_list = ["invoice_id", "file_format"]

    params = {}
    for param in params_list:
        try:
            params[param] = req.params[param]
        except KeyError as exc:
            message = f"No {param} parameter in the request."
            raise DownloadBlobError(
                exception_type="KeyError",
                details=f"KeyError: {param}",
                message=message,
                status_code=http_client.BAD_REQUEST,
            ) from exc

    log.debug(msg=f"Parameters of the request {req} read successfully.")
    return params
