"""Sets up CosmosDB connection."""
import http.client as http_client
import logging

from azure.cosmos import (
    exceptions as cosmos_exceptions,
    CosmosClient,
    DatabaseProxy,
    ContainerProxy,
)
from azure.core import exceptions as azure_exceptions


from .custom_error import QueryCosmosDBError

log = logging.getLogger(name="log." + __name__)


def setup_cosmos_client(connection_string: str) -> CosmosClient:
    """
    Creates a CosmosClient instance from a connection string. This can be retrieved from the Azure portal.
    For full list of optional keyword arguments, see the CosmosClient constructor.

    Parameters:
        connection_string (str):
            The CosmosDB connection string.

    Returns:
        client (azure.cosmos.CosmosClient):
            A CosmosClient instance.

    Raises:
        QueryCosmosDBError:
            If failed to connect with host declared in AccountEndpoint. (exceptions.ServiceRequestError)
            If CosmosDB host URL is invalid. (exceptions.CosmosResourceNotFoundError)
            If request times out. (exceptions.CosmosClientTimeoutError)
            If input authorization token can't serve the request. (exceptions.CosmosHttpResponseError)

    """
    log.debug(msg="Setting up CosmosDB connection.")

    try:
        client = CosmosClient.from_connection_string(conn_str=connection_string)

    except azure_exceptions.ServiceRequestError as exc:
        custom_message = "Failed to connect with host declared in AccountEndpoint. Check connection string."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=http_client.NOT_FOUND,
        ) from exc
    except cosmos_exceptions.CosmosResourceNotFoundError as exc:
        custom_message = "CosmosDB host URL is invalid. Check connection string."
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
        custom_message = "Unauthorized. The input authorization token can't serve the request. Check connection string."
        raise QueryCosmosDBError(
            exception_type=exc.__class__.__name__,
            details=exc.message,
            message=custom_message,
            status_code=exc.status_code,  # type: ignore
        ) from exc

    log.debug(msg="CosmosDB connection set up succesfully.")
    return client


def setup_database_client(client: CosmosClient, database_id: str) -> DatabaseProxy:
    """
    Retrieve an existing CosmosDB database with the ID (name).

    Parameters:
        client (azure.cosmos.CosmosClient):
            A CosmosClient instance.
        database_id (str):
            The ID (name) of the  CosmosDB database to read.

    Returns:
        database (azure.cosmos.DatabaseProxy):
            A DatabaseProxy instance representing the retrieved database.

    Raises:
        QueryCosmosDBError:
            If database is not found. (exceptions.CosmosResourceNotFoundError)
    """
    log.debug(msg="Setting up CosmosDB DatabaseProxy.")

    try:
        database = client.get_database_client(database=database_id)
    except cosmos_exceptions.CosmosResourceNotFoundError as exc:
        custom_message = f"CosmosDB database {database_id} was not found."
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

    log.debug(msg="CosmosDB DatabaseProxy set up succesfully.")

    return database


def setup_container_client(
    database: DatabaseProxy, container_id: str
) -> ContainerProxy:
    """
    Gets a CosmosDB ContainerProxy instance for a container with specified ID (name).

    Parameters:
        database (azure.cosmos.DatabaseProxy):
            A DatabaseProxy instance representing the retrieved database.
        container_id (str):
            The ID (name) of the container to be retrieved.

    Returns:
        container (azure.cosmos.ContainerProxy):
            A ContainerProxy instance representing the retrieved database.

    Raises:
        None. ContainerProxy instance is not a live object. Whether it exists or not is not checked\
        until a query is run and query items are unpacked from retrieved Iterable.
    """

    log.debug(msg="Setting up CosmosDB ContainerProxy.")

    try:
        container = database.get_container_client(container=container_id)
    except cosmos_exceptions.CosmosResourceNotFoundError as exc:
        custom_message = f"CosmosDB container {container_id} was not found."
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

    log.debug(msg="CosmosDB ContainerProxy set up succesfully.")

    return container


def main(connection_string: str, database_id: str, container_id: str) -> ContainerProxy:
    """
    Sets up CosmosDB connection and returns a ContainerProxy instance for a container with specified ID (name):\n
        Creates a CosmosClient instance from the parameter 'connection_string'.\n
        Retrieves an existing CosmosDB database with the parameter 'database_id'.\n
        Gets a CosmosDB ContainerProxy for a container with the specified parameter 'container_id'.\n

    Parameters:
        connection_string (str):
            The CosmosDB connection string.
        database_id (str):
            The ID (name) of the  CosmosDB database to read.
        container_id (str):
            The ID (name) of the container to be retrieved.

    Returns:
        container (azure.cosmos.ContainerProxy):
            A ContainerProxy instance representing the retrieved database.

    Raises:
        QueryCosmosDBError:
            If failed to connect with host declared in AccountEndpoint.
                in function: setup_cosmos_client;
                from exception: azure_exceptions.ServiceRequestError
            If CosmosDB host URL is invalid.
                in function: setup_cosmos_client;
                from exception: cosmos_exceptions.CosmosResourceNotFoundError
            If request times out.
                in function: setup_cosmos_client;
                from exception: cosmos_exceptions.CosmosClientTimeoutError
            If input authorization token can't serve the request.
                in function: setup_cosmos_client;
                from exception: cosmos_exceptions.CosmosHttpResponseError
            If database is not found.
                in function: setup_database_client;
                from exception: cosmos_exceptions.CosmosResourceNotFoundError


    """

    cosmos_client = setup_cosmos_client(connection_string=connection_string)

    database_proxy = setup_database_client(
        client=cosmos_client,
        database_id=database_id,
    )

    container_proxy = setup_container_client(
        database=database_proxy,
        container_id=container_id,
    )

    log.info(msg="CosmosDB connection set up succesfully.")
    return container_proxy
