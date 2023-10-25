"""Sets up connection with azure BLOB storage."""
import http.client as http_client
import logging
import sys

from azure.storage.blob import (
    BlobServiceClient,
    ContainerClient,
    BlobClient,
    StorageStreamDownloader,
)
import azure.core.exceptions as azure_exceptions

from .custom_error import DownloadBlobError


log = logging.getLogger(name="log." + __name__)


def create_blob_service_client(conn_str: str) -> BlobServiceClient:
    """Creates BlobServiceClient object.

    Parameters:
        conn_str (str): BLOB storage connection string.

    Returns:
        client (BlobServiceClient): BlobServiceClient object.

    Raises:
        None. BlobServiceClient is a local object and does not make any calls to the Azure Storage Blob service.
    """
    log.debug(msg="Creating BLOB service client.")
    client = BlobServiceClient.from_connection_string(conn_str=conn_str)
    log.debug(msg="BLOB service client created.")

    return client


def create_blob_container_client(
    blob_service_client: BlobServiceClient, container: str
) -> ContainerClient:
    """
    Creates ContainerClient object.

    Args:
        client (BlobServiceClient): BlobServiceClient object.
        container (str): BLOB storage container name.

    Returns:
        ContainerClient: ContainerClient object.

    Raises:
        None. ContainerClient is a local object and does not make any calls to the Azure Storage Blob service.
    """
    log.debug(msg="Creating ContainerClient object.")
    container_client = blob_service_client.get_container_client(container=container)
    log.debug(msg="ContainerClient object created.")

    return container_client


def get_blob_client(container_client: ContainerClient, file_name: str) -> BlobClient:
    """Get a client to interact with the specified blob. The blob need not already exist.

    Parameters:
        container_client (ContainerClient): ContainerClient object.
        file_name (str): .xml BLOB file name.

    Returns:
        blob_client (BlobClient): BlobClient object.

    Raises:
        None. BlobClient is a local object and does not make any calls to the Azure Storage Blob service.
    """
    log.debug(msg="Creating BlobClient object.")
    blob_client = container_client.get_blob_client(blob=file_name)
    log.debug(msg=f"BlobClient object created for {file_name}.")

    return blob_client


def download_blob(
    blob_client: BlobClient, timeout: int
) -> StorageStreamDownloader[bytes]:
    """Downloads a blob to the StorageStreamDownloader (memory).

    Parameters:
        blob_client (BlobClient): BlobClient object.
        timeout (int): timeout in seconds.

    Returns:
        blob (StorageStreamDownloader[bytes]): StorageStreamDownloader object.

    Raises:
        DownloadBlobError: if specified blob is not found or if there is a problem with the request.
    """
    log.debug(msg="Downloading blob.")
    try:
        blob = blob_client.download_blob(timeout=timeout)
    except (
        azure_exceptions.ResourceNotFoundError,
        azure_exceptions.ServiceRequestError,
    ) as exc:
        raise DownloadBlobError(
            exception_type=str(object=exc.__class__.__name__),
            details=str(object=exc.exc_value),
            message=exc.exc_msg,
            status_code=http_client.INTERNAL_SERVER_ERROR,
        ) from exc

    log.debug(msg="Blob downloaded.")

    return blob


def read_blob(blob: StorageStreamDownloader[bytes]) -> bytes:
    """Reads blob content to bytes.

    Parameters:
        blob (StorageStreamDownloader[bytes]): StorageStreamDownloader object.

    Returns:
        invoice (bytes): Invoice in bytes.

    Raises:
        #TODO: add exception docstring

    """
    log.debug(msg="Reading blob.")
    try:
        invoice = blob.readall()
    except Exception as exc:  # pylint: disable=W0703
        message = "Failed to read blob object."
        raise DownloadBlobError(
            exception_type=exc.__class__.__name__,
            details=str(object=sys.exc_info()),
            message=message,
            status_code=http_client.INTERNAL_SERVER_ERROR,
        ) from exc

    log.debug(msg="Blob read.")
    return invoice


def main(
    connection_string: str, container: str, invoice_id: str, timeout: int = 90
) -> bytes:
    """Downloads xml file from BLOB storage.

    Parameters:
        connection_string (str): BLOB storage connection string.
        container (str): BLOB storage container name.
        invoice_id (str): Invoice id.
        timeout (int, optional): Timeout in seconds. Defaults to 90.

    Returns:
        xml_bytes (bytes): Invoice in bytes.


    """
    file_name = invoice_id + ".xml"

    blob_service_client = create_blob_service_client(conn_str=connection_string)

    container_client = create_blob_container_client(
        blob_service_client=blob_service_client, container=container
    )

    blob_client = get_blob_client(
        container_client=container_client, file_name=file_name
    )

    blob = download_blob(blob_client=blob_client, timeout=timeout)

    xml_bytes = read_blob(blob=blob)

    return xml_bytes
