import json
import logging
import jsonschema
from typing import List, Dict
from django.core.exceptions import BadRequest
from rest_framework.exceptions import APIException
from . import prompts
from .processor import ConnectionProcessor
from common_utils.utils import get_env_var, send_post_request, parse_json

from common_utils.utils import (
    get_env_var,
    send_post_request,
    generate_uuid,
    validate_result,
    parse_json,
    read_json_file,
)

# Configuration
ENV = get_env_var("ENV")
MAX_RETRIES_ADD_CONNECION = int(get_env_var("MAX_RETRIES_ADD_CONNECION"))
WORK_DIR = (
    get_env_var("WORK_DIR") if ENV.lower() == "local" else get_env_var("GIT_WORK_DIR")
)
API_URL = get_env_var("API_URL")
QUESTIONNAIRE_JSON_SCHEMA_PATH = get_env_var(
    "QUESTIONNAIRE_JSON_SCHEMA_PATH_ADD_CONNECTION"
)
CONNECTION_JSON_SCHEMA_PATH = get_env_var("CONNECTION_JSON_SCHEMA_PATH_ADD_CONNECTION")
ENDPOINT_JSON_SCHEMA_PATH = get_env_var("ENDPOINT_JSON_SCHEMA_PATH_ADD_CONNECTION")
PARAMETER_JSON_SCHEMA_PATH = get_env_var("PARAMETER_JSON_SCHEMA_PATH_ADD_CONNECTION")
IMPORT_CONFIGS_PATH = get_env_var("IMPORT_CONFIGS_PATH_ADD_CONNECTION")
DATASOURCES_CONFIG_SCHEMA_PATH = get_env_var(
    "DATASOURCES_CONFIG_SCHEMA_PATH_ADD_CONNECTION"
)

# Logger setup
logger = logging.getLogger("django")
initialized_requests = set()
processor = ConnectionProcessor()


class ConnectionsInteractor:
    def __init__(self):
        logger.info("Initializing ConnectionsInteractor...")

    def clear_context(self, chat_id):
        # Validate input
        try:
            # Clear chat history
            processor.chat_history.clear_chat_history(chat_id)
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
                return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            logger.error(
                "An error occurred while clearing the context: %s", e, exc_info=True
            )
            raise APIException("An error occurred while clearing the context.", e)

    def chat(self, token, chat_id, user_endpoint, return_object, question):
        # Validate input
        self.validate_chat_input(chat_id, return_object, question)

        try:
            if return_object == prompts.Keys.IMPORT_CONNECTION.value:
                return self.handle_import_connection(token, chat_id, question)
            
            if return_object == prompts.Keys.CONNECTIONS.value:
                return self.handle_generate_connection(chat_id, question)
            
            if return_object == prompts.Keys.ENDPOINTS.value:
                return self.handle_generate_endpoint(chat_id, question)
            
            if return_object == prompts.Keys.PARAMETERS.value:
                return self.handle_generate_parameter(chat_id, question)
            
            if return_object == prompts.Keys.SOURCES.value:
                return self.handle_additional_sources(question)

            else:
                result = processor.ask_question(chat_id, question)
                return {"answer": result}

        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)

    def validate_chat_input(self, chat_id, return_object, question):
        if not all([chat_id, return_object, question]):
            raise BadRequest("Invalid input. All parameters are required.")

    def handle_import_connection(self, token, chat_id, question):
        connection_data = self.generate_connection_data(chat_id, question)
        ds_id = connection_data["dataSources"][0]["id"]
        self.save_data(token, connection_data)
        return {"success": True, "datasource_id": ds_id}
    
    def handle_generate_connection(self, chat_id, question):
        connection_data = self.generate_connection_data(chat_id, question)
        #connection_data = json.dumps(connection_data, indent=4)
        return connection_data

    def handle_generate_endpoint(self, chat_id, question):
        parsed_questionnaire = self.fill_in_questionnaire(chat_id, question)
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]
        generate_endpoints_prompt = f"Analyze the connection {connection_name} with base_url {connection_base_url} API document. "+f"Analyze the user requirement {question}. "+"Generate com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto endpoint config for {endpoints}. "+"Return only the DTO JSON list."
        
        endpoints_dto = self.generate_endpoints_dto(
            chat_id, connection_endpoints, generate_endpoints_prompt
        )
        return endpoints_dto

    def handle_generate_parameter(self, chat_id, question):
        parsed_questionnaire = self.fill_in_questionnaire(chat_id, question)
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]
        generate_endpoints_prompt = f"Analyze the connection {connection_name} with base_url {connection_base_url} API document. "+f"Analyze the user requirement {question}. " + f"Generate HttpParameterDto parameter config for {connection_endpoints}. "+"Return only the parameter DTO JSON as a JSON List."
        parameter_dto = self.generate_parameter_dto(chat_id, generate_endpoints_prompt)
        return parameter_dto

    def handle_additional_sources(self, question):
        urls = question.split(", ")
        return processor.load_additional_sources(urls)

    def construct_ai_question(self, user_endpoint, question, return_object):
        current_endpoint = f"Current endpoint: {user_endpoint}." if user_endpoint else ""
        return f"{question}. {current_endpoint} \n {prompts.RETURN_DATA.get(return_object, '')}"

    def log_and_raise_error(self, message, exception):
        logger.error(f"{message}: %s", exception, exc_info=True)
        raise APIException(message, exception)

    def generate_connection_data(self, chat_id: str, question: str):
        parsed_questionnaire = self.fill_in_questionnaire(chat_id, question)
        connection_data = self.process_connection(chat_id, parsed_questionnaire)
        return connection_data

    def process_connection(self, chat_id: str, parsed_questionnaire: dict):
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]
        generate_connection_prompt = (
            f"Write com.cyoda.plugins.datasource.dtos.connection.HttpConnectionDetailsDto "
            f"connection config for API {connection_name} with base_url {connection_base_url}. "
            "Return only the DTO JSON."
        )
        connection_dto = self.generate_connection_dto(
            chat_id, generate_connection_prompt
        )
        generate_endpoints_prompt = "Generate com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto endpoint configs for endpoints: {endpoints}. Return only the DTO JSON list."
        endpoints_dto = self.generate_endpoints_dto(
            chat_id, connection_endpoints, generate_endpoints_prompt
        )

        return self.build_result_connection(
            f"{WORK_DIR}/{DATASOURCES_CONFIG_SCHEMA_PATH}",
            connection_name,
            connection_dto,
            endpoints_dto,
        )

    def generate_dto(self, chat_id: str, prompt: str, schema_path: str):
        try:
            result = processor.ask_question(chat_id, prompt)
            return self.validate_and_parse_json(chat_id, result, f"{WORK_DIR}/{schema_path}")
        except Exception as e:
            logger.error(f"Error generating DTO for schema {schema_path}: %s", e)
            raise


    def fill_in_questionnaire(self, chat_id: str, question: str):
        prompt = f"Fill in Connections Questionnaire json based on the user question: {question}. Add necessary parameters. Return only Questionnaire json."
        return self.generate_dto(chat_id, prompt, QUESTIONNAIRE_JSON_SCHEMA_PATH)
    
    def generate_connection_dto(self, chat_id: str, prompt: str):
        return self.generate_dto(chat_id, prompt, CONNECTION_JSON_SCHEMA_PATH)

    def generate_endpoints_dto(self, chat_id: str, endpoints_list: List[any], prompt: str):
        endpoint_configs = []
        try:
            endpoint_prompt = prompt.replace("{endpoints}", str(endpoints_list))
            endpoint_configs.extend(self.generate_dto(chat_id, endpoint_prompt, ENDPOINT_JSON_SCHEMA_PATH))
            endpoint_configs = [config for config in endpoint_configs if config["method"] in ["POST_BODY", "GET"]]
        except Exception as e:
            logger.error("Error generating endpoint DTO: %s", e)
        return endpoint_configs

    def generate_parameter_dto(self, chat_id: str, prompt: str):
        try:
            result = processor.ask_question(chat_id, prompt)
            parsed_result = parse_json(result)
            parameters_list = []
            if isinstance(parsed_result, str):
                parsed_result = f"[{parsed_result}]" if not parsed_result.startswith("[") else parsed_result
                parameters_list = json.loads(parsed_result)
            else:
                parameters_list = parsed_result
            parameters_configs = []
            logger.info(parameters_list)
            for parameter in parameters_list:
                try:
                    parameters_configs.append(self.validate_and_parse_json(chat_id, json.dumps(parameter), f"{WORK_DIR}/{PARAMETER_JSON_SCHEMA_PATH}"))
                except Exception as e:
                    logger.error("Error generating endpoint DTO: %s", e)
            return parameters_configs
        except Exception as e:
                logger.error("Error generating parameter DTO: %s", e)


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

    def save_data(self, token: str, data: Dict):
        path = f"{IMPORT_CONFIGS_PATH}"
        data = json.dumps(data, indent=4)
        logger.info(f"Data prepared for import: {data}")
        try:
            response = send_post_request(
                token=token, api_url=API_URL, path=path, data=data, json=None
            )
            logger.info(f"Data saved successfully: {response}")
            return response
        except Exception as e:
            logger.error("Error saving data: %s", e)
            raise

    def validate_and_parse_json(
        self,
        chat_id: str,
        data: str,
        schema_path: str,
        max_retries: int = MAX_RETRIES_ADD_CONNECION,
    ):
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
                attempt += 1
                return json.loads(parsed_data)
            except jsonschema.exceptions.ValidationError as e:
                attempt += 1
                logger.warning(
                    f"JSON validation failed on attempt {attempt + 1} with error: {e.message}"
                )
                if attempt < max_retries:
                    question = (
                        f"Retry the last step. JSON validation failed with error: {e.message}. "
                        "Return only the DTO JSON."
                    )
                    retry_result = processor.ask_question(chat_id, question)
                    parsed_data = parse_json(retry_result)
            except Exception as e:
                logger.error("Maximum retry attempts reached. Validation failed.")
            finally:
                attempt += 1
        logger.error("Maximum retry attempts reached. Validation failed.")
        raise ValueError("JSON validation failed after retries.")
