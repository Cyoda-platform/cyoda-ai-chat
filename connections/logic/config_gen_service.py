import logging
from .processor import ConnectionProcessor
from common_utils.utils import get_env_var, send_get_request, send_post_request, send_put_request

logger = logging.getLogger('django')


processor = ConnectionProcessor()
# todo not thread safe - will replace later
initialized_requests = set()

API_URL = get_env_var("API_URL")
GET_CONNECTION_CONFIG_PATH = get_env_var("GET_CONNECTION_CONFIG_PATH")
POST_CHECK_CONNECTION_PATH = get_env_var("POST_CHECK_CONNECTION_PATH")
POST_SAVE_DATA_PATH = get_env_var("POST_SAVE_DATA_PATH")
POST_SAVE_SCHEMA_PATH = get_env_var("POST_SAVE_SCHEMA_PATH")
  
    
class ConfiGenerationError(Exception):
    """Custom exception class for errors."""
    pass


class ConfiGenerationService:
    def __init__(self):
        logger.info("Initializing...")


    def ingest_data(self, token: str, request):
        try:
            ds_id = request.query_params.get("datasource_id")
            operation = request.query_params.get("operation")

            ds_data = self.get_datasource_data(token, ds_id)
            endpoint, connection = self.get_endpoint_and_connection(ds_data, operation)
            ingestion_data = self.process_endpoint(token, endpoint, connection)

            self.ingest_data_based_on_schema(token, request, ingestion_data)

        except Exception as e:
            logger.error(f"An error occurred during data ingestion: {str(e)}")
            raise DataIngestionError(f"Data ingestion failed: {str(e)}") from e


    def get_datasource_data(self, token: str, ds_id: str) -> dict:
        """Fetches and returns the datasource data."""
        ds_response = send_get_request(token, API_URL, f"{GET_CONNECTION_CONFIG_PATH}/{ds_id}")
        if ds_response and ds_response.status_code == 200:
            return ds_response.json()
        raise DataIngestionError("Failed to retrieve datasource configuration")


    def get_endpoint_and_connection(self, ds_data: dict, operation: str):
        """Extracts and returns the endpoint and connection based on the operation."""
        operation_map = {endpoint["operation"]: endpoint for endpoint in ds_data.get("endpoints", [])}
        endpoint = operation_map.get(operation)

        if not endpoint:
            raise DataIngestionError("Operation not found in datasource configuration")

        connection_idx = endpoint.get("connectionIndex")
        connection = ds_data.get("connections", [{}])[connection_idx]

        return endpoint, connection


    def process_endpoint(self, token: str, endpoint: dict, connection: dict) -> dict:
        """Processes the endpoint and returns the ingestion data."""
        endpoint_request = {
            "type": "HTTP",
            "connectionDetails": connection,
            "endpointDetailsDto": endpoint,
            "userParameters": [],
        }

        endpoint_response = send_post_request(
            token=token, api_url=API_URL, path=POST_CHECK_CONNECTION_PATH, data=None, json=endpoint_request
        )

        if endpoint_response and endpoint_response.status_code == 200:
            return endpoint_response.json().get('responseContent')

        raise DataIngestionError("Failed to get a valid response from POST request")


    def ingest_data_based_on_schema(self, token: str, request, ingestion_data: dict):
        """Handles the data ingestion based on the schema flag."""
        schema_flag = request.query_params.get("schema") == "true"
        data_format = request.query_params.get("dataFormat")
        entity_name = request.query_params.get("entityName")
        model_version = request.query_params.get("modelVersion")
        entity_type = request.query_params.get("entityType")

        if schema_flag:
            self.save_schema_and_lock(token, data_format, entity_name, model_version, ingestion_data)
        else:
            self.save_data(token, data_format, entity_type, entity_name, model_version, ingestion_data)


    def save_schema_and_lock(self, token: str, data_format: str, entity_name: str, model_version: str, ingestion_data: dict):
        """Saves the schema and locks it."""
        ingestion_response = send_post_request(
            token=token,
            api_url=API_URL,
            path=f"{POST_SAVE_SCHEMA_PATH}/import/{data_format}/SAMPLE_DATA/{entity_name}/{model_version}",
            data=ingestion_data,
            json=None
        )

        if ingestion_response and ingestion_response.status_code == 200:
            lock_schema_response = send_put_request(
                token=token,
                api_url=API_URL,
                path=f"{POST_SAVE_SCHEMA_PATH}/{entity_name}/{model_version}/lock",
                data=None,
                json=None
            )
            if lock_schema_response and lock_schema_response.status_code == 200:
                logger.info("Schema locked successfully")
            else:
                raise DataIngestionError("Failed to lock the schema")
        else:
            raise DataIngestionError("Failed to save the schema")


    def save_data(self, token: str, data_format: str, entity_type: str, entity_name: str, model_version: str, ingestion_data: dict):
        """Saves the ingestion data."""
        ingestion_response = send_post_request(
            token=token,
            api_url=API_URL,
            path=f"{POST_SAVE_DATA_PATH}/{data_format}/{entity_type}/{entity_name}/{model_version}",
            data=ingestion_data,
            json=None
        )

        if ingestion_response and ingestion_response.status_code == 200:
            logger.info("Ingestion succeeded")
        else:
            raise DataIngestionError("Failed to ingest data")

