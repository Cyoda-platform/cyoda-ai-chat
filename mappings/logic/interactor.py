import json
import logging
from rest_framework.exceptions import APIException
import common_utils
from common_utils.config import API_URL
from common_utils.utils import parse_json
from .processor import MappingProcessor
from . import prompts

logger = logging.getLogger('django')

# Sets to keep track of initialized script and columns, not thread-safe - will be replaced later
initialized_mappings = set()
mappings_cache = {}

class MappingsInteractor:
    """
    A class that interacts with mappings for a chat system.
    """

    def __init__(self, processor: MappingProcessor):
        """
        Initializes the MappingsInteractor instance.
        """
        logger.info("Initializing MappingsInteractor...")
        self.processor = processor

    def initialize_mapping(self, token, chat_id, ds_input, entity):
        """
        Initializes a mapping for the given chat ID, data source input, and entity.

        :param chat_id: The ID of the chat session.
        :param ds_input: The data source input.
        :param entity: The entity to initialize the mapping for.
        :return: A Response indicating the result of the initialization.
        """
        logger.info(
            "Mapping parameters: Entity=%s, Data source input=%s", entity, ds_input
        )

        model_name, model_version = entity.split(".")
        entity_response = common_utils.utils.send_get_request(token, API_URL,
                                                              f"treeNode/model/export/SIMPLE_VIEW/{model_name}/{model_version}")
        entity_body = entity_response.json()

        mappings_cache[chat_id] = ds_input
        questions = [
            prompts.MAPPINGS_INITIAL_ADD_ENTITY.format(entity, entity_body),
            prompts.MAPPINGS_INITIAL_PROMPT_SCRIPT.format(entity, entity, ds_input),
        ]

        logger.info("Mapping init questions list: %s", questions)
        return self._initialize(chat_id, initialized_mappings, questions)

    def chat(self, chat_id, user_script, return_object, question):
        current_script = (
            f"Current script: {user_script}."
            if user_script and return_object != prompts.Keys.AUTOCOMPLETE.value
            else ""
        )
        logger.info("Current script: %s", user_script)
        return_string = prompts.RETURN_DATA.get(return_object, "")
        ai_question = f"{question}. {current_script} {return_string}"
        logger.info("Asking question: %s", ai_question)
        if return_object == prompts.Keys.TRANSFORMERS.value:
            return self._process_transformers(question)
        result = self.processor.ask_question(chat_id, ai_question)
        return self._process_return_object(chat_id, return_object, result)

    def clear_context(self, chat_id):
        """
        Clears the context for the given chat ID.

        :param chat_id: The ID of the chat session.
        :return: A Response indicating the result of the context clearing.
        """
        self.processor.chat_history.clear_chat_history(chat_id)
        items_to_remove = [initialized_mappings]
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
                    result = self.processor.ask_question(chat_id, question)
                    logger.info(result)
                initialized_set.add(chat_id)
                return {"answer": f"{chat_id} initialization complete"}
            except Exception as e:
                logger.error(
                    "An error occurred during initialization: %s", e, exc_info=True
                )
                return {"error": str(e)}

    def _process_return_object(self, chat_id, return_object, result):
        if return_object in [
            prompts.Keys.RANDOM.value,
            prompts.Keys.CODE.value,
            prompts.Keys.AUTOCOMPLETE.value,
        ]:
            response_data = {"answer": result}
        elif return_object == prompts.Keys.SCRIPT.value:
            response_data = self._process_script_return(chat_id, result)
        elif return_object == prompts.Keys.TRANSFORMERS.value:
            response_data = self._process_transformers(result)
        elif return_object == prompts.Keys.COLUMNS.value:
            try:
                response_data = json.loads(result)
            except json.JSONDecodeError as e:
                raise APIException("Invalid JSON response from processor", e)

        else:
            raise APIException("Invalid return object")
        return response_data

    def _process_script_return(self, chat_id, script_result):
        try:
            script_result = parse_json(script_result)
            script = {
                    "script": {"body": script_result, "inputSrcPaths": []}
            }
            return script
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from processor: %s", e, exc_info=True)
            # Handle JSON decoding error appropriately
            raise APIException("Invalid JSON response from processor", e)
        
    def generate_paths(self, data, current_path=""):
        logger.info("CURRENT_DATA")
        logger.info(data)
        paths = []
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{current_path}/{key}" if current_path else key
                if isinstance(value, (dict, list)):
                    paths.extend(self.generate_paths(value, new_path))
                else:
                    paths.append(new_path)
        elif isinstance(data, list):
            for i in range(len(data)):
                new_path = f"{current_path}/*"
                if isinstance(data[i], (dict, list)):
                    paths.extend(self.generate_paths(data[i], new_path))
                else:
                    paths.append(new_path)

        return paths

    def _get_input_scr_params(self, chat_id):
        refine_question = prompts.SCRIPT_REFINE_PROMPT
        refine_result = self.processor.ask_question(chat_id, refine_question)
        logger.info("Refined question: %s", refine_result)
        try:
            input_src_paths = json.loads(refine_result)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from processor: %s", e, exc_info=True)
            # Handle JSON decoding error appropriately
            raise APIException("Invalid JSON response from processor", e)
        return input_src_paths

    def _process_transformers(self, question):
        result = self._extract_date_info(question)
        template = {
            "transformer": {
                "type": "COMPOSITE",
                "children": [
                    {"type": "SINGLE", "transformerKey": result, "parameters": []}
                ],
            }
        }
        return template if result else None

    def _remove_from_set(self, chat_id, initialized_set):
        """
        A private method that removes a chat ID from the given set.

        :param chat_id: The ID of the chat session.
        :param initialized_set: The set to remove the chat ID from.
        """
        if chat_id in initialized_set:
            initialized_set.remove(chat_id)

    def _extract_date_info(self, question):
        data = json.loads(question)
        dst_path_type = data.get("dstCyodaColumnPathType", "")

        if dst_path_type == "java.lang.Integer":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToInt"
        elif dst_path_type == "java.lang.ToBoolean":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToBoolean"
        elif dst_path_type == "java.lang.Float":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToFloat"
        elif dst_path_type == "java.lang.Long":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToLong"
        elif dst_path_type == "java.lang.Byte":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToByte"
        elif dst_path_type == "java.lang.Short":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToShort"
        elif dst_path_type == "package java.math.BigDecimal":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToBigDecimal"
        elif dst_path_type == "java.lang.Double":
            return "com.cyoda.plugins.mapping.core.parser.valuetransformers.SourceObjectValueTransformer$ToDouble"
