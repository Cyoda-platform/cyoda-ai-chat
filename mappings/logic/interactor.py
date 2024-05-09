import json
import logging
from . import prompts
from .processor import MappingProcessor
from rest_framework.exceptions import APIException

# Initialize the processor and set the logging level
processor = MappingProcessor()
logger = logging.getLogger(__name__)

# Sets to keep track of initialized script and columns, not thread-safe - will be replaced later
initialized_columns = set()
initialized_script = set()
initialized_mappings = set()

class MappingsInteractor:
    """
    A class that interacts with mappings for a chat system.
    """

    def __init__(self):
        """
        Initializes the MappingsInteractor instance.
        """
        logger.info("Initializing MappingsInteractor...")

    def initialize_mapping(self, chat_id, ds_input, entity):
        """
        Initializes a mapping for the given chat ID, data source input, and entity.

        :param chat_id: The ID of the chat session.
        :param ds_input: The data source input.
        :param entity: The entity to initialize the mapping for.
        :return: A Response indicating the result of the initialization.
        """
        logger.info("Mapping parameters:")
        logger.info(entity)
        logger.info(ds_input)
        questions = [prompts.MAPPINGS_INITIAL_PROMPT.format(ds_input, entity, entity),
                     prompts.MAPPINGS_INITIAL_RELATIONS_PROMPT]
        logger.info(questions)
        return self._initialize(chat_id, initialized_mappings, questions)

    def initialize_script(self, chat_id):
        """
        Initializes the script for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the initialization.
        """
        return self._initialize(chat_id, initialized_script, [prompts.MAPPINGS_INITIAL_PROMPT_SCRIPT])

    def initialize_columns(self, chat_id):
        """
        Initializes the columns for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the initialization.
        """
        return self._initialize(
            chat_id, initialized_columns, [prompts.MAPPINGS_INITIAL_PROMPT_COLUMNS]
        )

    def chat(self, chat_id, user_script, return_object, question):
        self._initialize_return_object(chat_id, return_object)
        current_script = f"Current script: {user_script}." if user_script else ""
        logger.info(f"Current script: {user_script}")
        return_string = prompts.RETURN_DATA.get(return_object, "")
        ai_question = f"{question}. {current_script} {return_string}"
        logger.info(f"Asking question: {ai_question}")
        result = processor.ask_question(chat_id, ai_question)
        return self._process_return_object(chat_id, return_object, result)
    
    def clear_context(self, chat_id):
        """
        Clears the context for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the context clearing.
        """
        processor.chat_history.clear_chat_history(chat_id)
        items_to_remove = [initialized_columns, initialized_script, initialized_mappings]
        for item in items_to_remove:
            self._remove_from_set(chat_id, item)
        return {"message": f"Chat mapping with id {chat_id} cleared."}
    
    def _initialize(self, chat_id, initialized_set, questions):
        """
        A private method that initializes a resource for the given chat ID.

        :param chat_id: The ID of the chat session.
        :param initialized_set: The set to track the initialized resources.
        :param question: The prompt to ask the question.
        :return: A Response indicating the result of the initialization.
        """
        if chat_id not in initialized_set:
            try:
                for question in questions:
                    result = processor.ask_question(chat_id, question)
                    logger.info(result)
                initialized_set.add(chat_id)
                return {"answer": f"{chat_id} initialization complete"}
            except Exception as e:
                logger.error("An error occurred during initialization: %s", e, exc_info=True)
                return {"error": str(e)}

    def _initialize_return_object(self, chat_id, return_object):
        if return_object == "script" or return_object == "code" or return_object == "autocomplete":
            self.initialize_script(chat_id)
        # elif return_object == "columns":
        # self.initialize_columns(chat_id)

    def _process_return_object(self, chat_id, return_object, result):
        response_data = {}
        if return_object in ["random", "code", "autocomplete"]:
            response_data = {"answer": result}
        elif return_object == "script":
            response_data = self._process_script_return(chat_id, result)
        elif return_object == "transformers":
            response_data = self._process_transformers(result)
        elif return_object == "columns":
            try:
                response_data = json.loads(result)
            except json.JSONDecodeError as e:
                raise APIException("Invalid JSON response from processor", e)

        else:
            raise APIException("Invalid return object")
        return response_data

    def _process_script_return(self, chat_id, script_result):
        try:
            script_result_json = json.loads(script_result)
            if (
                "script" in script_result_json
                and script_result_json["script"] is not None
            ):
                logging.info("Script included in response")
                return script_result_json
            else:
                input_src_paths = self._get_input_scr_params(chat_id)
                script = {
                    "script": {"body": script_result, "inputSrcPaths": input_src_paths}
                }
                return script
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e, exc_info=True)
            # Handle JSON decoding error appropriately
            raise APIException("Invalid JSON response from processor", e)

    def _get_input_scr_params(self, chat_id):
        refine_question = prompts.SCRIPT_REFINE_PROMPT
        refine_result = processor.ask_question(chat_id, refine_question)
        logger.info(f"Refined question: {refine_result}")
        try:
            input_src_paths = json.loads(refine_result)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from processor: %s", e, exc_info=True)
            # Handle JSON decoding error appropriately
            raise APIException("Invalid JSON response from processor", e)
        return input_src_paths

    def _process_transformers(self, result):
        template = {
            "transformer": {
                "type": "COMPOSITE",
                "children": [
                    {"type": "SINGLE", "transformerKey": result, "parameters": []}
                ],
            }
        }
        return template

    def _remove_from_set(self, chat_id, initialized_set):
        """
        A private method that removes a chat ID from the given set.

        :param chat_id: The ID of the chat session.
        :param initialized_set: The set to remove the chat ID from.
        """
        if chat_id in initialized_set:
            initialized_set.remove(chat_id)