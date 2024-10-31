import json
import logging

from rest_framework.exceptions import APIException
import common_utils
from common_utils.config import API_URL
from common_utils.utils import parse_json
from config_generator.config_interactor import ConfigInteractor
from .processor import MappingProcessor
from . import prompts

logger = logging.getLogger('django')
chat_id_prefix = "mappings"

class MappingsInteractor(ConfigInteractor):
    """
    A class that interacts with mappings for a chat system.
    """

    def __init__(self, processor: MappingProcessor):

        super().__init__(processor)
        logger.info("Initializing MappingsInteractor...")
        self.processor = processor

    def initialize_mapping(self, token, chat_id, ds_input, entity_name):

        logger.info(
            "Mapping parameters: Entity=%s, Data source input=%s", entity_name, ds_input
        )
        super().initialize_chat(token, chat_id, str(ds_input))
        model_name, model_version = entity_name.split(".")
        entity_response = common_utils.utils.send_get_request(token, API_URL,
                                                              f"treeNode/model/export/SIMPLE_VIEW/{model_name}/{model_version}")
        entity_body = entity_response.json()['model']
        questions = [
            prompts.MAPPINGS_INITIAL_PROMPT_SCRIPT.format(ds_input, entity_body),
        ]
        logger.info("Mapping init questions list: %s", questions)
        return self._initialize(chat_id, questions)

    def chat(self, token, chat_id, return_object, question, user_script):
        super().chat(token, chat_id, question, return_object, user_script)
        current_script = (
            f"Current script: {user_script}."
            if user_script and return_object != prompts.Keys.AUTOCOMPLETE.value
            else ""
        )
        logger.info("Current script: %s", user_script)
        return_string = prompts.RETURN_DATA.get(return_object, "")
        ai_question = f"{question}. {current_script} {return_string}"
        logger.info("Asking question: %s", ai_question)
        if return_object == prompts.Keys.SOURCES.value:
            return self.handle_additional_sources(chat_id, question)
        if return_object == prompts.Keys.TRANSFORMERS.value:
            return self._process_transformers(question)
        result = self.processor.ask_question(chat_id, ai_question)
        response = self._process_return_object(chat_id, return_object, result)
        return {"success": True, "message": response}

    def _initialize(self, chat_id, questions):
        try:
            for question in questions:
                result = self.processor.ask_question(chat_id, question)
                logger.info(result)
            return {"success": True, "message": chat_id}
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
            response_data = result
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

    def handle_additional_sources(self, chat_id, question):
        urls = question.split(", ")
        return self.processor.load_additional_rag_sources(urls)

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
