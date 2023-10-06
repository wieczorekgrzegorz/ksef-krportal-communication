# query_cosmosDB

[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The query_cosmosDB function is an Azure Function that queries a Cosmos DB database and returns the results as a JSON response.

## Usage

To use the query_cosmosDB function, you need to provide a JSON payload in the body of the HTTP request. The payload should contain the following fields:

- **query**: The SQL query to execute. Warning: call SELECT must contain **id** in unchanged form for the app to work

Here's an example payload:

```python
{
    "query": "SELECT c.id, c.NIP FROM c WHERE c.NIP = '9999999999'"
}
```

As per [Azure documentation](https://learn.microsoft.com/en-us/azure/cosmos-db/concepts-limits#sql-query-limits), maximum length of SQL query is 512 KB.

To send the HTTP request, you can use any HTTP client library or tool, such as **curl** or **requests**. Here's an example using curl:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"database_id": "my_database", "container_id": "my_container", "query": "SELECT * FROM c WHERE c.name = '\''John'\''"}' \
  http://localhost:7071/api/query_cosmosDB
```

The function will return a JSON response with the results of the query. If the query is successful, the response will have a status code of 200 and a body containing the query results. If the query fails, the response will have a status code of 500 and a body containing an error message.

## Configuration

The **query_cosmosDB** function requires the following environment variables to be set:

- **CONNECTION_STRING**: The connection string for the Cosmos DB account.
- **DATABASE_ID**: The ID of the Cosmos DB database to query.
- **CONTAINER_ID**: The ID of the Cosmos DB container to query.

These environment variables can be set in the Azure portal or using the **local.settings.json** file when running the function locally.

## Development

To develop and test the **query_cosmosDB** function locally, you can use the Azure Functions Core Tools. First, make sure you have Python 3.7 or later installed, as well as the Azure Functions Core Tools.

Then, clone the repository and navigate to the **query_cosmosDB** directory:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/query_cosmosDB
```

Install the required dependencies:
```pip install -r requirements.txt```

Set the required environment variables in a local.settings.json file:

```python
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "CONNECTION_STRING": "your-connection-string",
    "DATABASE_ID": "your-database-id",
    "CONTAINER_ID": "your-container-id"
  }
}
```

Run the function locally using the Azure Functions Core Tools:

```func start```

You can then send HTTP requests to the function using curl or another HTTP client.
