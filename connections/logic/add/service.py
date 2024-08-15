import json
import logging
from typing import List
from rest_framework.exceptions import APIException
from common_utils.utils import parse_json
import jsonschema

from .processor import ImportConnectionProcessor

from common_utils.utils import (
    get_env_var,
    send_post_request,
    generate_uuid,
    validate_result,
    parse_json,
    read_json_file,
)

# Configuration
WORK_DIR = get_env_var("WORK_DIR")
API_URL = get_env_var("API_URL")
QUESTIONNAIRE_JSON_SCHEMA_PATH = "data/v1/connections/connections_questionnaire.json"
CONNECTION_JSON_SCHEMA_PATH = "data/v1/connections/connection_json_schema.json"
ENDPOINT_JSON_SCHEMA_PATH = "data/v1/connections/endpoint_json_schema.json"
IMPORT_CONFIGS_PATH = "data-source-config/import-cobi-config?cleanBeforeImport=false&doPostProcess=false"
DATASOURCES_CONFIG_SCHEMA_PATH = "data/v1/connections/connection_dto_template.json"
# Logger setup
logger = logging.getLogger("django")

# Processor Initialization
processor = ImportConnectionProcessor()
initialized_requests = set()


class ImportConnectionInteractor:
    def __init__(self):
        logger.info("Initializing...")

    def clear_context(self, chat_id):
        try:
            processor.chat_history.clear_chat_history(chat_id)
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
            return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            logger.error(
                "An error occurred while clearing the context: %s", e, exc_info=True
            )
            raise APIException("An error occurred while clearing the context.", e)

    def chat(self, token: str, question: str):
        parsed_questionnaire = self.fill_in_questionnaire(question)
        connection_data = self.process_connection(parsed_questionnaire)
        ds_id = connection_data["dataSources"][0]["id"]
        self.save_data(token, connection_data)
        return ds_id

    def fill_in_questionnaire(self, question: str):
        try:
            prompt = f"Fill in Connections Questionnaire json based on the user question: {question}. Return only Questionnaire json."
            questionnaire_result = processor.ask_question(id, prompt)
            return self.validate_and_parse_json(
                questionnaire_result, f"{WORK_DIR}/{QUESTIONNAIRE_JSON_SCHEMA_PATH}"
            )
        except Exception as e:
            logger.error("Error processing questionnaire: %s", e)
            raise

    def process_connection(self, parsed_questionnaire: dict):
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]

        connection_dto = self.generate_connection_dto(
            connection_name, connection_base_url
        )
        endpoints_dto = self.generate_endpoints_dto(connection_endpoints)

        return self.build_result_connection(
            f"{WORK_DIR}/{DATASOURCES_CONFIG_SCHEMA_PATH}",
            connection_name,
            connection_dto,
            endpoints_dto,
        )
        
    def validate_and_parse_json(self, data: str, schema_path: str, max_retries: int = 1):
        """
        Parses and validates JSON data against a given schema. If validation fails,
        retries the operation up to `max_retries` times by asking the processor to retry.

        :param data: The JSON data as a string.
        :param schema_path: The path to the JSON schema file.
        :param max_retries: The maximum number of retries if validation fails.
        :return: Parsed JSON data as a dictionary.
        :raises ValueError: If JSON validation fails after the maximum retries.
        """
        try:
            parsed_data = parse_json(data)
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError("Invalid JSON data provided.") from e

        attempt = 0
        while attempt <= max_retries:
            try:
                validate_result(parsed_data, schema_path)
                logger.info(f"JSON validation successful on attempt {attempt + 1}.")
                return json.loads(parsed_data)
            except jsonschema.exceptions.ValidationError as e:
                logger.warning(
                    f"JSON validation failed on attempt {attempt + 1} with error: {e.message}"
                )
                if attempt < max_retries:
                    attempt += 1
                    question = (
                        f"Retry the last step. JSON validation failed with error: {e.message}. "
                        "Return only the DTO JSON."
                    )
                    retry_result = processor.ask_question(id, question)
                    parsed_data = parse_json(retry_result)
        logger.error("Maximum retry attempts reached. Validation failed.")
        raise ValueError("JSON validation failed after retries.")


    def generate_connection_dto(self, connection_name: str, connection_base_url: str):
        try:
            prompt = (
                f"Write com.cyoda.plugins.datasource.dtos.connection.HttpConnectionDetailsDto "
                f"connection config for API {connection_name} with base_url {connection_base_url}. "
                "Return only the DTO JSON."
            )
            connection_result = processor.ask_question(id, prompt)
            return self.validate_and_parse_json(
                connection_result, f"{WORK_DIR}/{CONNECTION_JSON_SCHEMA_PATH}"
            )
        except Exception as e:
            logger.error("Error generating connection DTO: %s", e)
            raise

    def generate_endpoints_dto(self, endpoints_list: List[str]):
        endpoint_configs = []
        for endpoint_name in endpoints_list:
            try:
                prompt = (
                    f"Generate com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto "
                    f"endpoint config for {endpoint_name}. Return only the DTO JSON."
                )
                endpoint_result = processor.ask_question(id, prompt)
                endpoint_configs.append(
                    self.validate_and_parse_json(
                        endpoint_result, f"{WORK_DIR}/{ENDPOINT_JSON_SCHEMA_PATH}"
                    )
                )
            except Exception as e:
                logger.error("Error generating endpoint DTO: %s", e)
        return endpoint_configs

    def build_result_connection(
        self, template_path: str, name: str, connection: dict, endpoints: List[dict]
    ):
        try:
            data = read_json_file(template_path)
            data["dataSources"][0]["name"] = name
            data["dataSources"][0]["id"] = str(generate_uuid())
            data["dataSources"][0]["connections"].append(connection)
            data["dataSources"][0]["endpoints"].extend(endpoints)
            return data
        except Exception as e:
            logger.error("Error building result connection: %s", e)
            raise

    def save_data(self, token: str, data: str):
        path = f"{IMPORT_CONFIGS_PATH}"
        data = json.dumps(data, indent=4)
        try:
            response = send_post_request(
                token=token, api_url=API_URL, path=path, data=data, json=None
            )
            logger.info(f"Data saved successfully: {response}")
            return response
        except Exception as e:
            logger.error("Error saving data: %s", e)
            raise
