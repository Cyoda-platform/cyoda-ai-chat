import json
import logging
import uuid
from typing import List, Dict
from django.core.exceptions import BadRequest
from rest_framework.exceptions import APIException

from config_generator.config_interactor import ConfigInteractor
from . import prompts
from .processor import ConnectionProcessor
from common_utils.config import (
    MAX_RETRIES_ADD_CONNECTION,
    WORK_DIR,
    API_URL,
    QUESTIONNAIRE_JSON_SCHEMA_PATH,
    CONNECTION_JSON_SCHEMA_PATH,
    ENDPOINT_JSON_SCHEMA_PATH,
    PARAMETER_JSON_SCHEMA_PATH,
    IMPORT_CONFIGS_PATH,
    DATASOURCES_CONFIG_SCHEMA_PATH
)
from common_utils.utils import (
    send_post_request,
    generate_uuid,
    parse_json,
    read_json_file,
    validate_and_parse_json
)

logger = logging.getLogger("django")

class ConnectionsInteractor(ConfigInteractor):
    def __init__(self, processor: ConnectionProcessor):
        super().__init__(processor)
        logger.info("Initializing ConnectionsInteractor...")
        self.processor = processor

    def chat(self, token: str, chat_id: str, return_object: str, question: str, user_data: str) -> dict:
        super().chat(token, chat_id, question, return_object, user_data)
        try:
            self.validate_chat_input(chat_id, return_object, question)
        except ValueError as e:
            logger.error(f"Input validation failed: {e}")
            raise Exception(f"Invalid input: {e}") from e

        try:
            # Define a mapping from return_object values to handler methods
            handler_mapping = {
                prompts.Keys.IMPORT_CONNECTION.value: self.handle_import_connection,
                prompts.Keys.CONNECTIONS.value: self.handle_generate_connection,
                prompts.Keys.ENDPOINTS.value: self.handle_generate_endpoint,
                prompts.Keys.PARAMETERS.value: self.handle_generate_parameter,
                prompts.Keys.SOURCES.value: self.handle_additional_sources,
            }

            # Retrieve the appropriate handler based on return_object
            handler = handler_mapping.get(return_object)

            if handler:
                # Check if the handler requires the token parameter
                if return_object == prompts.Keys.IMPORT_CONNECTION.value:
                    return {"success": True, "message": handler(token=token, chat_id=chat_id, question=question)}
                else:
                    return {"success": True, "message": handler(chat_id, question)}
            else:
                # Default action if no handler is found
                result = self.processor.ask_question(chat_id, question)
                return {"success": True, "message": result}

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
        # connection_data = json.dumps(connection_data, indent=4)
        return connection_data

    def handle_generate_endpoint(self, chat_id, question):
        parsed_questionnaire = self.fill_in_questionnaire(chat_id, question)
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]
        generate_endpoints_prompt = f"Analyze the connection {connection_name} with base_url {connection_base_url} API document. " + f"Analyze the user requirement {question}. " + "Generate com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto endpoint config for {endpoints}. " + "Return only the DTO JSON list."

        endpoints_dto = self.generate_endpoints_dto(
            chat_id, connection_endpoints, generate_endpoints_prompt
        )
        return endpoints_dto

    def handle_generate_parameter(self, chat_id, question):
        parsed_questionnaire = self.fill_in_questionnaire(chat_id, question)
        connection_name = parsed_questionnaire["connection_name"]
        connection_base_url = parsed_questionnaire["connection_base_url"]
        connection_endpoints = parsed_questionnaire["connection_endpoints"]
        generate_endpoints_prompt = f"Analyze the connection {connection_name} with base_url {connection_base_url} API document. " + f"Analyze the user requirement {question}. " + f"Generate HttpParameterDto parameter config for {connection_endpoints}. " + "Return only the parameter DTO JSON as a JSON List."
        parameter_dto = self.generate_parameter_dto(chat_id, generate_endpoints_prompt)
        return parameter_dto

    def handle_additional_sources(self, chat_id, question):
        urls = question.split(", ")
        return self.processor.load_additional_sources(urls)

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
            result = self.processor.ask_question(chat_id, prompt)
            return validate_and_parse_json(self.processor, chat_id, result, f"{WORK_DIR}/{schema_path}", MAX_RETRIES_ADD_CONNECTION)
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
            result = self.processor.ask_question(chat_id, prompt)
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
                    parameters_configs.append(validate_and_parse_json(self.processor, chat_id, json.dumps(parameter),
                                                                           f"{WORK_DIR}/{PARAMETER_JSON_SCHEMA_PATH}", MAX_RETRIES_ADD_CONNECTION))
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
            data["dataSources"][0]["name"] = name + "_" + str(uuid.uuid1())
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
