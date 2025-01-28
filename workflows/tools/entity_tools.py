
import json
import logging
import jsonschema
from common_utils.utils import get_env_var, send_get_request, send_post_request
from workflows.logic.processor import WorkflowProcessor
from common_utils.utils import parse_json, read_json_file, validate_result

logger = logging.getLogger('django')
token_store = {}
API_URL = get_env_var("API_URL")
GET_WORKFLOW_LIST_PATH = get_env_var("GET_WORKFLOW_LIST_PATH")
POST_SAVE_SCHEMA_PATH = get_env_var("POST_SAVE_SCHEMA_PATH")
MAX_RETRIES_ADD_CONNECTION = int(get_env_var("MAX_RETRIES_ADD_CONNECTION"))

ENV = get_env_var("ENV")
WORK_DIR = (
    get_env_var("WORK_DIR") if ENV.lower() == "local" else get_env_var("GIT_WORK_DIR")
)

WORKFLOW_CLASS_NAME = "com.cyoda.tdb.model.treenode.TreeNodeEntity"
rag_processor = WorkflowProcessor()

class EntityTools:

    def __init__(self):
        logger.info("Initializing RagProcessor v1...")
        
    
    def get_entity_by_id(self):
        """Function to get an entity"""
        pass

    def get_current_state(self):
        """Function to get the current state."""
        pass

    def get_next_transition(self):
        """Function to get the next transition."""
        pass

    def launch_transition(self):
        """Function to launch a transition."""
        pass

    def get_workflows_list(self, token, chat_id):
        """Function to get the list of workflows."""
        path = f"{GET_WORKFLOW_LIST_PATH}{WORKFLOW_CLASS_NAME}" #
        logger.info(path)
        response = send_get_request(token, API_URL, path)
        prompt = f"Analyse the response from the data source and return a list of available workflow names with short descriptions. The response {response.content}"
        workflows = rag_processor.ask_question(chat_id, prompt)
        return workflows
    
    def get_workflow_data(self, token, chat_id, workflow_name):
        """Function to get the list of workflows."""
        path = f"{GET_WORKFLOW_LIST_PATH}{WORKFLOW_CLASS_NAME}" #
        logger.info(path)
        response = send_get_request(token, API_URL, path)
        #move somewhere else
        prompt = (
            f"You are given the workflow name '{workflow_name}' and the workflows configuration page content: {response.content}. "
            f"Please provide clear instructions to the user on what data they need to submit to proceed with the chosen workflow. "
            f"Ensure that the instructions are specific to the configuration details provided. Here is an example format for your response."
        )
        workflows = rag_processor.ask_question(chat_id, prompt)
        return workflows
    
    
    def validate_workflow_data(self, token, chat_id,  workflow_data):
        """Function to get the list of workflows."""
        path = f"{GET_WORKFLOW_LIST_PATH}{WORKFLOW_CLASS_NAME}" #
        logger.info(path)
        response = send_get_request(token, API_URL, path)
        #move somewhere else
        prompt = (
            f"You are given the user specified workflow data '{workflow_data}'. Validate that it is sufficient to proceed with the chosen workflow. Use description of this workflow in the configuration page content: {response.content}. Be concise and return only the missing data. Say if data is sufficient and we can proceed with the workflow"
        )
        workflows_validation = rag_processor.ask_question(chat_id, prompt)
        return workflows_validation

    def save_workflow_entity(self, token, chat_id, workflow_name, workflow_data):
        #store token for the session - need to improve logic
        token_store[chat_id] = token
        workflow_schema_path= f"data/v1/workflows/{workflow_name}.json"
        workflow_schema = read_json_file(f"{WORK_DIR}/{workflow_schema_path}")
        prompt = (
            f"You are given the user specified chat_id '{chat_id}', workflow_name '{workflow_name}' and workflow data '{workflow_data}'. Based on this data fill in workflow_schema json: {workflow_schema}. Return only workflow_schema json."
        )
        result_data = rag_processor.ask_question(chat_id, prompt)
        workflow_schema_validation_path= f"{WORK_DIR}/data/v1/workflows/{workflow_name}_schema.json"
        parsed_data = self.validate_and_parse_json(chat_id, result_data, workflow_schema_validation_path, MAX_RETRIES_ADD_CONNECTION)
        schema_data = json.dumps(parsed_data)
        path = f"entity/new/{parsed_data["dataFormat"]}/{parsed_data["entityType"]}/{parsed_data["workflow_name"]}/1"
        response = send_post_request(token, API_URL, path, schema_data, None)
        return response.json()


    def validate_and_parse_json(
        self,
        chat_id: str,
        data: str,
        schema_path: str,
        max_retries: int = MAX_RETRIES_ADD_CONNECTION,
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
                    retry_result = rag_processor.ask_question(chat_id, question)
                    parsed_data = parse_json(retry_result)
            except Exception as e:
                logger.error("Maximum retry attempts reached. Validation failed.")
            finally:
                attempt += 1
        logger.error("Maximum retry attempts reached. Validation failed.")
        raise ValueError("JSON validation failed after retries.")