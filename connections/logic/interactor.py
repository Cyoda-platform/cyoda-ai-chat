import json
import logging
from django.core.exceptions import BadRequest
from rest_framework.exceptions import APIException
from common_utils.utils import parse_json
from . import prompts
from .processor import ConnectionProcessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
processor = ConnectionProcessor()
# todo not thread safe - will replace later
initialized_requests = set()


class ConnectionsInteractor:
    def __init__(self):
        logger.info("Initializing...")

    def clear_context(self, chat_id):
        # Validate input
        try:
            # Clear chat history
            processor.chat_history.clear_chat_history(chat_id)

            # Remove chat_id from initialized_requests if it exists
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
                return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            logger.error(
                "An error occurred while clearing the context: %s", e, exc_info=True
            )
            raise APIException("An error occurred while clearing the context.", e)

    def chat(self, chat_id, user_endpoint, return_object, question):
        # Validate input
        if not all([chat_id, return_object, question]):
            raise BadRequest("Invalid input. All parameters are required.")

        try:
            if return_object == prompts.Keys.SOURCES.value:
                urls = question.split(', ')
                return processor.load_additional_sources(urls)
            # Initialize current_script and return_string
            if chat_id not in initialized_requests:
                return self._initialize_connection_request(
                    chat_id, return_object, question
                )
            # Construct ai_question
            current_endpoint = (
                f"Current endpoint: {user_endpoint}." if user_endpoint else ""
            )
            ai_question = f"{question}. {current_endpoint} \n {prompts.RETURN_DATA.get(return_object, '')}"
            logger.info("Sending AI request %s", ai_question)
            # Ask question to processor
            result = processor.ask_question(chat_id, ai_question)
            # Handle different return_objects
            return self._handle_return_object(return_object, result)
        except Exception as e:
            logger.error(
                "An error occurred while processing the chat: %s", e, exc_info=True
            )
            raise APIException("An error occurred while processing the chat.", e)

    def _handle_return_object(self, return_object, result):
        if return_object == prompts.Keys.RANDOM.value:
            return {"answer": result}
        elif return_object == prompts.Keys.ENDPOINTS.value:
            return self._process_endpoint_result(result)
        elif return_object == prompts.Keys.PARAMETERS.value:
            return self._process_parameters_result(result)
        else:
            try:
                result_dict = json.loads(result)
                return result_dict
            except json.JSONDecodeError as e:
                logger.error(
                    "Invalid JSON response from processor: %s", e, exc_info=True
                )
                return {
                    "error": "Invalid JSON response from processor",
                    "details": str(e),
                }

    def _initialize_connection_request(self, chat_id, return_object, question):
        if not all([chat_id, question]):
            raise BadRequest("Invalid input. chat_id and question are required.")

        try:
            logger.info("Initializing request: ")
            if return_object != prompts.Keys.ENDPOINTS.value:
                return {"answer": "Please, initialize the endpoints request first."}
            # Ask questions to the processor and handle the responses
            prompts_list = [(prompts.INITIAL_API_ANALYSIS_PROMPT)]

            for prompt in prompts_list:
                question_formatted = prompt.format(question)
                result = self._ask_processor_question(chat_id, question_formatted)
                logger.info("Prompt %s returns result %s", prompt, result)
            init_endpoints_result = self._ask_processor_question(
                chat_id, prompts.INITIAL_API_PROMPT
            )
            logger.info("Prompt second returns result %s", init_endpoints_result)
            # Process the endpoint result
            resp = self._process_endpoint_result(init_endpoints_result)
            initialized_requests.add(chat_id)
            return resp
        except Exception as e:
            logger.error(
                "An error occurred while initializing the connection request: %s",
                e,
                exc_info=True,
            )
            raise APIException(
                "An error occurred while initializing the connection request.", e
            )

    def _ask_processor_question(self, chat_id, question):
        try:
            result = processor.ask_question(chat_id, question)
            return result
        except Exception as e:
            logger.error(
                "An error occurred while asking the processor a question: %s",
                e,
                exc_info=True,
            )
            raise

    def _process_parameters_result(self, script_result):
        try:
            script_result = parse_json(script_result)
            # Parse the JSON response
            parameters_result_json = json.loads(script_result)
            logger.info(parameters_result_json)
            result = self.process_template_parameters(
                template=None, res_params=parameters_result_json
            )
            return result
        except json.JSONDecodeError as e:
            raise APIException("Invalid JSON response from processor", e)
        except Exception as e:
            raise APIException(
                "An error occurred while processing the endpoint result.", e
            )

    def _process_endpoint_result(self, script_result):
        try:
            script_result = parse_json(script_result)
            # Parse the JSON response
            endpoint_result_json = json.loads(script_result)

            # Check if the JSON response contains the 'operation' key
            if (
                "operation" in endpoint_result_json
                and endpoint_result_json["operation"] is not None
            ):
                # Process the endpoint result
                template = self._create_endpoint_template(endpoint_result_json)
                template = self._populate_endpoint_template(
                    endpoint_result_json, template
                )
                return template
            else:
                return {"answer": endpoint_result_json}
        except json.JSONDecodeError as e:
            raise APIException("Invalid JSON response from processor", e)
        except Exception as e:
            raise APIException(
                "An error occurred while processing the endpoint result.", e
            )

    def _create_endpoint_template(self, endpoint_result_json):
        # Create a template with default values
        template = {
            "@bean": "com.cyoda.plugins.datasource.dtos.endpoint.HttpEndpointDto",
            "chainings": [],
            "operation": "",
            "cache": {"parameters": [], "ttl": 0},
            "connectionIndex": 0,
            "type": "test",
            "query": "",
            "method": "",
            "parameters": [],
            "bodyTemplate": "",
            "connectionTimeout": 300,
            "readWriteTimeout": 300,
        }
        keys_to_check = [
            "operation",
            "query",
            "bodyTemplate",
            "connectionTimeout",
            "readWriteTimeout",
        ]
        for key in keys_to_check:
            if key in endpoint_result_json and endpoint_result_json[key] is not None:
                template[key] = endpoint_result_json[key]
        if (
            "method" in endpoint_result_json
            and endpoint_result_json["method"] is not None
        ):
            template["method"] = (
                "POST_BODY"
                if endpoint_result_json["method"].startswith("POST")
                else "GET"
            )
        return template

    def _populate_endpoint_template(self, endpoint_result_json, template):
        if (
            "parameters" in endpoint_result_json
            and endpoint_result_json["parameters"] is not None
        ):
            res_params = endpoint_result_json["parameters"]

            template_parameters = self.process_template_parameters(template, res_params)
            template["parameters"] = template_parameters
        logger.info("template==")
        logger.info(template)
        return template

    def process_template_parameters(self, template, res_params):
        template_parameters = []
        param_keys_to_check = [
            "name",
            "defaultValue",
            "secure",
            "required",
            "template",
            "templateValue",
            "excludeFromCacheKey",
            "type",
            "optionValues",
        ]
        for res_param in res_params:
            param_template = {
                "name": "",
                "defaultValue": "",
                "secure": "false",
                "required": "true",
                "excludeFromCacheKey": "false",
                "type": "",
                "optionValues": [],
            }
            for key in param_keys_to_check:
                if key in res_param and res_param[key] is not None:
                    param_template[key] = res_param[key]
            param_template = self._process_endpoint_param(
                template, res_param, param_template
            )
            logger.info("parameters==")
            logger.info(param_template)
            template_parameters.append(param_template)
        return template_parameters

    def _process_endpoint_param(self, template, res_param, param_template):
        if any(arg is None for arg in [res_param, param_template]):
            raise ValueError("Res_param, and param_template cannot be None")

        try:
            # Process the parameter based on the method type
            if template is not None:
                param_template["type"] = self._process_method_type(
                    template, param_template
                )
            param_template["templateValue"] = self._process_template_value(res_param)
            param_template["template"] = (
                "true" if param_template["templateValue"] else "false"
            )
            return param_template
        except Exception as e:
            logger.error(
                "An error occurred while processing endpoint parameter: %s",
                e,
                exc_info=True,
            )
            raise

    def _process_template_value(self, res_param):
        if "templateValue" in res_param:
            return res_param["templateValue"]
        elif "template" in res_param and str(res_param["template"]).startswith("$"):
            return res_param["template"]
        return None

    def _process_method_type(self, template, param_template):
        if template["method"] == "POST_BODY":
            return "REQUEST_BODY_VARIABLE"
        elif template["method"] == "GET":
            return self._process_get_method(template, param_template)

    def _process_get_method(self, template, param_template):
        param_placeholder_name = f"{{{param_template['name']}}}"
        if "query" in template and param_placeholder_name in template["query"]:
            # Check if the value associated with the key does not start with $
            path_placeholder = f"${param_placeholder_name}"
            if path_placeholder not in template["query"]:
                logger.info(template["query"])
                template["query"] = template["query"].replace(
                    param_placeholder_name, path_placeholder
                )
            return "PATH_VARIABLE"
        else:
            return "REQUEST_PARAM"
