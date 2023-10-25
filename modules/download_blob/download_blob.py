"""Facilitates process of downloading xml file from BLOB storage."""
import http.client as http_client
import logging
import sys
from typing import Callable

import azure.functions as func
from lxml import etree


from .modules import read_params, download_xml, create_pdf
from .modules.custom_error import DownloadBlobError

log = logging.getLogger(name="log." + __name__)


def main(  # pylint: disable=R0913
    req: func.HttpRequest,
    blob_connection_string: str,
    blob_container_name: str,
    exception_handler: Callable,
    xslt_transformer: etree.XSLT,
    default_body: str = "Unexpected error, please contact function administrator.",
    default_status_code: int = http_client.INTERNAL_SERVER_ERROR,
) -> tuple[str | bytes, int]:
    """
    Facilitates process of downloading xml file from BLOB storage.

    Args:
        blob_connection_string (str): connection string to BLOB storage
        blob_container_name (str): name of BLOB storage container
        exception_handler (Callable): function that handles exceptions
        default_body (str, optional): string returned in case of unhandled exception.\
            Defaults to "Unexpected error, please contact function administrator.".
        default_status_code (int, optional): status code returned in case of unhandled exception.\
            Defaults to http_client.INTERNAL_SERVER_ERROR.

    Returns:
        tuple[str | bytes, int]: http response body and status code
    """
    status_code = default_status_code
    body = default_body

    try:
        params = read_params.main(req=req)

        xml_bytes = download_xml.main(
            connection_string=blob_connection_string,
            container=blob_container_name,
            invoice_id=params["invoice_id"],
        )

        if params["file_format"] == "pdf":
            return (
                create_pdf.main(xml_bytes=xml_bytes, xslt_transformer=xslt_transformer),
                http_client.OK,
            )

        return xml_bytes, http_client.OK

    except DownloadBlobError as exc:
        return exception_handler(exc=exc)

    except Exception:  # pylint: disable=W0718
        # if unhandled exception, return default HTTP response with error details and use default status code (500)
        exc_type, exc_value, exc_traceback = sys.exc_info()  # pylint: disable=W0612
        body = str(object={"exception": exc_type.__name__, "message": exc_value})  # type: ignore
        # "except Exceptions" is enough to know there is an exception with a name and a value
        return body, status_code
