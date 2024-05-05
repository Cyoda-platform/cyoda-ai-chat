import json
import logging
from rest_framework.response import Response
from rest_framework import status
from . import prompts
from .processor import MappingProcessor

# Initialize the processor and set the logging level
processor = MappingProcessor()
logging.basicConfig(level=logging.INFO)

# Sets to keep track of initialized script and columns
initialized_columns = set()
initialized_script = set()

class MappingsInteractor:
    """
    A class that interacts with mappings for a chat system.
    """

    def __init__(self):
        """
        Initializes the MappingsInteractor instance.
        """
        logging.info("Initializing MappingsInteractor...")

    def initialize_mapping(self, chat_id, ds_input, entity):
        """
        Initializes a mapping for the given chat ID, data source input, and entity.

        :param chat_id: The ID of the chat session.
        :param ds_input: The data source input.
        :param entity: The entity to initialize the mapping for.
        :return: A Response indicating the result of the initialization.
        """
        return self._initialize(chat_id, initialized_columns, prompts.MAPPINGS_INITIAL_PROMPT, entity)

    def initialize_script(self, chat_id):
        """
        Initializes the script for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the initialization.
        """
        return self._initialize(chat_id, initialized_script, prompts.MAPPINGS_INITIAL_PROMPT_SCRIPT, "script")

    def initialize_columns(self, chat_id):
        """
        Initializes the columns for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the initialization.
        """
        return self._initialize(chat_id, initialized_columns, prompts.MAPPINGS_INITIAL_PROMPT_COLUMNS, "columns")

    def _initialize(self, chat_id, initialized_set, prompt, entity):
        """
        A private method that initializes a resource for the given chat ID.

        :param chat_id: The ID of the chat session.
        :param initialized_set: The set to track the initialized resources.
        :param prompt: The prompt to ask the question.
        :param entity: The entity to initialize.
        :return: A Response indicating the result of the initialization.
        """
        if chat_id not in initialized_set:
            try:
                question = prompt.format(entity) if callable(prompt) else prompt
                result = processor.ask_question(chat_id, question)
                logging.info(result)
                initialized_set.add(chat_id)
                return Response({"answer": f"{entity} initialization complete"}, status=status.HTTP_200_OK)
            except Exception as e:
                logging.error("An error occurred during initialization: %s", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def chat(self, chat_id, user_script, return_object, question):
        self.initialize_return_object(chat_id, return_object)
        current_script = f"Current script: {user_script}." if user_script else ""
        return_string = prompts.RETURN_DATA.get(return_object, "")
        ai_question = f"{question}. {current_script} {return_string}"
        logging.info(f"Asking question: {ai_question}")
        result = processor.ask_question(chat_id, ai_question)
        return self.process_return_object(chat_id, return_object, result)

    def initialize_return_object(self, chat_id, return_object):
        if return_object == "script":
            self.initialize_script(chat_id)
        #elif return_object == "columns":
        #self.initialize_columns(chat_id)

    def process_return_object(self, chat_id, return_object, result):
        response_data = {}
        if return_object in ["random", "code", "autocomplete"]:
            response_data = {"answer": result}
        elif return_object == "script":
            response_data = self.process_script_return(chat_id, result)
        elif return_object == "transformers":
            response_data = self.process_transformers(result)
        elif return_object == "columns":
            try:
                response_data = json.loads(result)
            except json.JSONDecodeError as e:
                logging.error("Invalid JSON response from processor %s", e)
                return Response(
                    {"error": "Invalid JSON response from processor", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            return Response(
                {"error": "Invalid return object"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(response_data, status=status.HTTP_200_OK)

    def process_script_return(self, chat_id, script_result):
        try:
            script_result_json = json.loads(script_result)
            if "script" in script_result_json and script_result_json["script"] is not None:
                logging.info("Script included in response")
                return script_result_json
            else:
                input_src_paths = self.get_input_scr_params(chat_id)
                script = {"script": {"body": script_result, "inputSrcPaths": input_src_paths}}
                return script
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
            # Handle JSON decoding error appropriately
            return Response(
                {"error": "Invalid JSON response from processor", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_input_scr_params(self, chat_id):
        refine_question = prompts.SCRIPT_REFINE_PROMPT
        refine_result = processor.ask_question(chat_id, refine_question)
        logging.info(f"Refined question: {refine_result}")
        try:
            input_src_paths = json.loads(refine_result)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
            # Handle JSON decoding error appropriately
            return Response(
                {"error": "Invalid JSON response from processor", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return input_src_paths

    def process_transformers(self, result):
        template = {
            "transformer": {
                "type": "COMPOSITE",
                "children": [
                    {"type": "SINGLE", "transformerKey": result, "parameters": []}
                ],
            }
        }
        return template



    def clear_context(self, chat_id):
        """
        Clears the context for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the context clearing.
        """
        processor.chat_history.clear_chat_history(chat_id)
        self._remove_from_set(chat_id, initialized_columns)
        self._remove_from_set(chat_id, initialized_script)
        return Response(
            {"message": f"Chat mapping with id {chat_id} cleared."},
            status=status.HTTP_200_OK,
        )

    def _remove_from_set(self, chat_id, initialized_set):
        """
        A private method that removes a chat ID from the given set.

        :param chat_id: The ID of the chat session.
        :param initialized_set: The set to remove the chat ID from.
        """
        if chat_id in initialized_set:
            initialized_set.remove(chat_id)

    
