import os
from pathlib import PurePath as path
import sys

os.environ["AZURE_COSMOSDB_CONNECTION_STRING"] = "mock_connection_string"
os.environ["DATABASE_ID"] = "mock_database_id"
os.environ["CONTAINER_ID"] = "mock_container_id"

test_CONTAINER_ID = os.environ["CONTAINER_ID"]


function_app_path = str(path(__file__).parents[1])

# adding main app folder to PATH
sys.path.insert(0, function_app_path)
