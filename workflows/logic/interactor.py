import logging
import json
import base64
import re
import httpx

from common_utils.utils import (
    send_get_request,
    send_put_request,
    validate_and_parse_json, read_json_file
)
from common_utils.config import (
    API_URL,
    WORK_DIR,
    MAX_RETRIES_GENERATE_WORKFLOW,
    WORKFLOW_SCHEMA_PATH,
    WORKFLOW_TRANSITIONS_SCHEMA_PATH
)
from config_generator.config_interactor import ConfigInteractor
from .workflow_gen_service import WorkflowGenerationService
from .processor import WorkflowProcessor
from . import prompts

logger = logging.getLogger('django')

chat_id_prefix = "workflow"

class WorkflowsInteractor(ConfigInteractor):
    def __init__(self, processor: WorkflowProcessor, workflow_generation_service: WorkflowGenerationService):
        super().__init__(processor)
        logger.info("Initializing WorkflowsInteractor...")
        self.workflow_generation_service = workflow_generation_service
        self.processor = processor

    def chat(self, token, chat_id, question, return_object, json_data):

        try:
            super().chat(token, chat_id, question, return_object, json_data)
            class_name = json_data.get("class_name")

            if not question or not class_name:
                return {"success": False, "message": "question or class_name is missing"}

            if return_object == prompts.Keys.GENERATE_WORKFLOW_FROM_URL.value:
                workflow_id = self._generate_workflow_from_image_url(chat_id, token, question, class_name)
                return {"success": True,
                        "message": f"Workflow id = {workflow_id}"}

            if return_object == prompts.Keys.GENERATE_WORKFLOW_FROM_IMAGE.value:
                image_file = json_data.get('file')
                if image_file is None:
                    return {"success": False, "message": "image_file is missing"}
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

            result = self.processor.ask_question(chat_id, question)
            return {"success": True, "message": f"{result}"}

        except Exception as e:
            raise e

    def parse_request_data(self, request):
        if 'multipart/form-data' in request.content_type:
            data = json.loads(request.data.get('json_data'))
            data['file'] = request.data.get('file')
            return data
        return request.data

    def _generate_workflow_from_image_url(self, chat_id, token, question, class_name):
        image_url, updated_question = self._extract_first_url(question)
        if not image_url:
            return {"success": False, "message": "No valid URL specified"}

        image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
        data = self.processor.ask_question_with_image(chat_id, updated_question, image_data)
        data = validate_and_parse_json(self.processor, chat_id, data, f"{WORK_DIR}/{WORKFLOW_SCHEMA_PATH}",
                                       MAX_RETRIES_GENERATE_WORKFLOW)
        return self.save_workflow_entity(token, data, class_name)

    def _generate_workflow_from_image_file(self, chat_id, token, question, class_name, image_file):
        encoded_image_data = base64.b64encode(image_file.read()).decode('utf-8')
        data = self.processor.ask_question_with_image(chat_id, question, encoded_image_data)
        data = validate_and_parse_json(self.processor, chat_id, data, f"{WORK_DIR}/{WORKFLOW_SCHEMA_PATH}",
                                       MAX_RETRIES_GENERATE_WORKFLOW)
        return self.save_workflow_entity(token, data, class_name)

    def _generate_workflow_from_text(self, chat_id, token, question, class_name):
        data_validated = validate_and_parse_json(self.processor, chat_id, question, f"{WORK_DIR}/{WORKFLOW_SCHEMA_PATH}",
                                        MAX_RETRIES_GENERATE_WORKFLOW)
        cyoda_dto_map = self.workflow_generation_service.parse_ai_to_cyoda_dto(data_validated, class_name)
        return self.workflow_generation_service.save_workflow(token, cyoda_dto_map)

    def _generate_transitions_from_text(self, chat_id, token, question, class_name, workflow_id):
        workflow_transitions_raw = send_get_request(token, API_URL,
                                                    f"platform-api/statemachine/persisted/workflows/{workflow_id}/transitions")
        existing_transitions = self._get_existing_transitions(workflow_transitions_raw.content)
        data = self.processor.ask_question(
            chat_id,
            f"{question}. Class name is {class_name}. Return only a json array of required transitions. Take into account that these transitions already exist: {json.dumps(existing_transitions)}. Return type = array"
        )
        new_transitions = validate_and_parse_json(self.processor, chat_id, data,
                                                  f"{WORK_DIR}/{WORKFLOW_TRANSITIONS_SCHEMA_PATH}",
                                                  MAX_RETRIES_GENERATE_WORKFLOW)
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
        return self.workflow_generation_service.generate_workflow_from_json(token, data, class_name)

    def _save_workflow_transitions(self, token, data, class_name, workflow_id):
        return self.workflow_generation_service.generate_workflow_transitions_from_json(token, data, class_name,
                                                                                        workflow_id)

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
        return self.processor.load_additional_sources(urls)
