import logging
import json
import base64
import jsonschema
import re

import httpx
from rest_framework.exceptions import APIException

from common_utils.utils import (
    get_env_var, send_get_request, send_put_request, validate_result, parse_json
)
from .workflow_gen_service import WorkflowGenerationService
from .processor import WorkflowProcessor
from . import prompts

# Initialize logging
logger = logging.getLogger('django')

# Configuration
API_URL = get_env_var("API_URL")
ENV = get_env_var("ENV")
WORK_DIR = get_env_var("WORK_DIR") if ENV.lower() == "local" else get_env_var("GIT_WORK_DIR")
MAX_RETRIES_GENERATE_WORKFLOW = int(get_env_var("MAX_RETRIES_GENERATE_WORKFLOW"))

# Services
workflow_generation_service = WorkflowGenerationService()
processor = WorkflowProcessor()
initialized_requests = set()


class WorkflowsInteractor:
    def __init__(self):
        logger.info("Initializing WorkflowsInteractor...")

    def clear_context(self, chat_id):
        try:
            processor.chat_history.clear_chat_history(chat_id)
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
                return {"message": f"Chat context with id {chat_id} cleared."}
            return {"message": f"Chat context with id {chat_id} was empty."}
        except Exception as e:
            self._log_and_raise_error("An error occurred while clearing the context", e)

    def _log_and_raise_error(self, message, exception):
        logger.error(f"{message}: %s", exception, exc_info=True)
        raise APIException(message, exception)

    def chat(self, request, token):
        json_data = self._parse_request_data(request)
        try:
            chat_id = json_data.get("chat_id")
            if not chat_id:
                return {"success": False, "message": "chat_id is missing"}

            return_object = json_data.get("return_object")
            if not return_object:
                return {"success": False, "message": "return_object is missing"}

            question = json_data.get("question")
            class_name = json_data.get("class_name")

            if not question or not class_name:
                return {"success": False, "message": "question or class_name is missing"}

            if return_object == prompts.Keys.GENERATE_WORKFLOW_FROM_URL.value:
                workflow_id = self._generate_workflow_from_image_url(chat_id, token, question, class_name)
                return {"success": True,
                        "message": f"Workflow id = {workflow_id}"}

            if return_object == prompts.Keys.GENERATE_WORKFLOW_FROM_IMAGE.value:
                image_file = request.data.get('file')
                workflow_id = self._generate_workflow_from_image_file(chat_id, token, question, class_name, image_file)
                return {"success": True,
                        "message": f"Workflow id = {workflow_id}"}

            if return_object == prompts.Keys.GENERATE_WORKFLOW.value:
                workflow_id = self._generate_workflow_from_text(chat_id, token, question, class_name)
                return {"success": True,
                        "message": f"Workflow id = {workflow_id}"}

            if return_object == prompts.Keys.SOURCES.value:
                self.handle_additional_sources(question)
                return {"success": True,
                        "message": f"{question} added"}

            if return_object == prompts.Keys.GENERATE_TRANSITION.value:
                workflow_id = json_data.get("workflow_id")
                if not workflow_id:
                    return {"success": False, "message": "workflow_id is missing"}
                workflow_id = self._generate_transitions_from_text(chat_id, token, question, class_name, workflow_id)
                return {"success": True,
                        "message": f"Workflow id = {workflow_id}"}
            result = processor.ask_question(chat_id, question)
            return {"success": True, "message": f"{result}"}

        except Exception as e:
            self._log_and_raise_error("An error occurred while processing the chat", e)

    def _parse_request_data(self, request):
        if 'multipart/form-data' in request.content_type:
            return json.loads(request.data.get('json_data'))
        return request.data

    def _generate_workflow_from_image_url(self, chat_id, token, question, class_name):
        image_url, updated_question = self._extract_first_url(question)
        if not image_url:
            return {"success": False, "message": "No valid URL specified"}

        image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
        data = processor.ask_question_with_image(chat_id, updated_question, image_data)
        data = self._validate_and_parse_json(chat_id, data, f"{WORK_DIR}/data/v1/workflows/workflow_schema.json")
        return self.save_workflow_entity(token, data, class_name)

    def _generate_workflow_from_image_file(self, chat_id, token, question, class_name, image_file):
        encoded_image_data = base64.b64encode(image_file.read()).decode('utf-8')
        data = processor.ask_question_with_image(chat_id, question, encoded_image_data)
        data = self._validate_and_parse_json(chat_id, data, f"{WORK_DIR}/data/v1/workflows/workflow_schema.json")
        return self.save_workflow_entity(token, data, class_name)

    def _generate_workflow_from_text(self, chat_id, token, question, class_name):
        data = processor.ask_question(chat_id, f"{question}. Class name is {class_name}")
        data = self._validate_and_parse_json(chat_id, data, f"{WORK_DIR}/data/v1/workflows/workflow_schema.json")
        return self.save_workflow_entity(token, data, class_name)

    def _generate_transitions_from_text(self, chat_id, token, question, class_name, workflow_id):
        workflow_transitions_raw = send_get_request(token, API_URL,
                                                    f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions")
        existing_transitions = self._get_existing_transitions(workflow_transitions_raw.content)
        data = processor.ask_question(
            chat_id,
            f"{question}. Class name is {class_name}. Return only a json array of required transitions. Take into account that these transitions already exist: {json.dumps(existing_transitions)}. Return type = array"
        )
        new_transitions = self._validate_and_parse_json(chat_id, data,
                                                        f"{WORK_DIR}/data/v1/workflows/workflow_transitions_schema.json")
        existing_names = set(transition["name"] for transition in existing_transitions)
        filtered_new_transitions = [transition for transition in new_transitions if
                                    transition["name"] not in existing_names]
        return self._save_workflow_transitions(token, filtered_new_transitions, class_name, workflow_id)

    def _get_existing_transitions(self, input_json):
        input_json = json.loads(input_json)
        return [
            {
                "name": item["name"],
                "description": item["description"],
                "start_state": item["startStateName"],
                "end_state": item["endStateName"]
            }
            for item in input_json["Data"]
        ]

    def _extract_first_url(self, question):
        url_pattern = r'https?://[^\s/$.?#].[^\s]*[^\s.,]'
        match = re.search(url_pattern, question)
        if match:
            url = match.group(0)
            updated_question = re.sub(re.escape(url), '', question).strip()
            return url, updated_question
        return None, question

    def save_workflow_entity(self, token, data, class_name):
        return workflow_generation_service.generate_workflow_from_json(token, data, class_name)

    def _save_workflow_transitions(self, token, data, class_name, workflow_id):
        return workflow_generation_service.generate_workflow_transitions_from_json(token, data, class_name, workflow_id)

    def get_next_transitions(self, token, workflow_id, entity_id, entity_class):
        next_transitions = send_get_request(token, API_URL,
                                            f"platform-api/entity/fetch/transitions?entityId={entity_id}&entityClass={entity_class}")
        all_transitions = send_get_request(token, API_URL,
                                           f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions")
        data = all_transitions.json()
        next_transitions_list = next_transitions.json()

        transitions = [
            {
                "name": transition["name"],
                "description": transition["description"]
            }
            for transition in data["Data"] if transition["name"] in next_transitions_list
        ]

        return {"transitions": transitions}

    def launch_transition(self, token, transition_name, entity_id, entity_class):
        launch_transition_path = f"platform-api/entity/transition?entityId={entity_id}&entityClass={entity_class}&transitionName={transition_name}"
        launch_transition_resp = send_put_request(token, API_URL, launch_transition_path)
        return launch_transition_resp.status_code == 200

    def handle_additional_sources(self, question):
        urls = question.split(", ")
        return processor.load_additional_sources(urls)

    def _validate_and_parse_json(
            self,
            chat_id: str,
            data: str,
            schema_path: str,
            max_retries: int = MAX_RETRIES_GENERATE_WORKFLOW,
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
                        f"Retry generating workflow. JSON validation failed with error: {e.message}. "
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
