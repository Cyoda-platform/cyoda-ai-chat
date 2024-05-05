import json
import logging
from django.http import (
    JsonResponse,
    HttpResponseServerError,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from . import prompts
from .processor import ConnectionProcessor

logger = logging.getLogger(__name__)
processor = ConnectionProcessor()
# todo not thread safe - will replace later
initialized_requests = set()


class ConnectionsInteractor:
    def __init__(self):
        logger.info("Initializing...")

    def initialize_connection(self, chat_id, ds_doc):
        if not chat_id or not ds_doc:
            return HttpResponseBadRequest(
                json.dumps(
                    {"error": "Invalid input. chat_id and ds_doc are required."}
                ),
                content_type="application/json",
            )
        try:
            # todo
            return JsonResponse(
                {"message": "Connection initialized successfully."}, status=200
            )
        except Exception as e:
            logger.error("An error occurred while initializing the connection: %s", e)
            return HttpResponseServerError(
                json.dumps(
                    {
                        "error": "An error occurred while initializing the connection.",
                        "details": str(e),
                    }
                ),
                content_type="application/json",
            )

    def clear_context(self, chat_id):
        # Validate input
        if not chat_id:
            return HttpResponseBadRequest(
                json.dumps({"error": "Invalid input. chat_id is required."}),
                content_type="application/json",
            )

        try:
            # Clear chat history
            processor.chat_history.clear_chat_history(chat_id)

            # Remove chat_id from initialized_requests if it exists
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
                return JsonResponse(
                    {"message": f"Chat context with id {chat_id} cleared."}, status=200
                )
            else:
                return HttpResponseNotFound(
                    json.dumps(
                        {"error": f"Chat context with id {chat_id} was not found."}
                    ),
                    content_type="application/json",
                )
        except Exception as e:
            logger.error("An error occurred while clearing the context: %s", e)
            return HttpResponseServerError(
                json.dumps(
                    {
                        "error": "An error occurred while clearing the context.",
                        "details": str(e),
                    }
                ),
                content_type="application/json",
            )

    def chat(self, chat_id, user_endpoint, return_object, question):
        # Validate input
        if not all([chat_id, user_endpoint, return_object, question]):
            return HttpResponseBadRequest(
                json.dumps({"error": "Invalid input. All parameters are required."}),
                content_type="application/json",
            )

        try:
            # Initialize current_script and return_string
            if chat_id not in initialized_requests:
                if return_object != "endpoints":
                    return JsonResponse(
                        {"answer": "Please, initialize the endpoints request first."},
                        status=200,
                    )
                initialized_requests.add(chat_id)
                resp = self.initialize_connection_request(chat_id, question)
                return JsonResponse(resp, status=200)

            # Construct ai_question
            current_endpoint = (
                f"Current endpoint: {user_endpoint}." if user_endpoint else ""
            )
            ai_question = f"{question}. {current_endpoint} \n {prompts.RETURN_DATA.get(return_object, '')}"
            logger.info(ai_question)

            # Ask question to processor
            result = processor.ask_question(chat_id, ai_question)

            # Handle different return_objects
            return self.handle_return_object(return_object, chat_id, result)
        except Exception as e:
            logger.error("An error occurred while processing the chat: %s", e)
            return HttpResponseServerError(
                json.dumps(
                    {
                        "error": "An error occurred while processing the chat.",
                        "details": str(e),
                    }
                ),
                content_type="application/json",
            )

    def handle_return_object(self, return_object, chat_id, result):
        if return_object == "random":
            return JsonResponse({"answer": result}, status=200)
        elif return_object == "endpoints":
            return JsonResponse(
                self.process_endpoint_result(chat_id, result), status=200
            )
        else:
            try:
                result_dict = json.loads(result)
                return JsonResponse(result_dict, status=200)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON response from processor: %s", e)
                return JsonResponse(
                    {
                        "error": "Invalid JSON response from processor",
                        "details": str(e),
                    },
                    status=500,
                )

    def initialize_connection_request(self, chat_id, question):
        # Validate input
        if not all([chat_id, question]):
            return HttpResponseBadRequest(
                json.dumps(
                    {"error": "Invalid input. chat_id and question are required."}
                ),
                content_type="application/json",
            )

        try:
            # Ask questions to the processor and handle the responses
            init_request_question = (prompts.INITIAL_REQUEST_ANALYSIS_PROMPT).format(
                question
            )
            init_request_result = self.ask_processor_question(
                chat_id, init_request_question
            )
            logger.info(init_request_result)
            init_params_question = (prompts.INITIAL_PARAMETERS_ANALYSIS_PROMPT).format(
                question
            )
            init_params_result = self.ask_processor_question(
                chat_id, init_params_question
            )
            logger.info(init_params_result)
            init_question = (
                (prompts.INITIAL_API_PROMPT).format(question)
                + " "
                + prompts.RETURN_DATA.get("endpoints")
            )
            init_endpoints_result = self.ask_processor_question(chat_id, init_question)

            # Process the endpoint result
            resp = self.process_endpoint_result(chat_id, init_endpoints_result)
            return JsonResponse(resp, status=200)
        except Exception as e:
            logger.error(
                "An error occurred while initializing the connection request: %s", e
            )
            return HttpResponseServerError(
                json.dumps(
                    {
                        "error": "An error occurred while initializing the connection request.",
                        "details": str(e),
                    }
                ),
                content_type="application/json",
            )

    def ask_processor_question(self, chat_id, question):
        try:
            result = processor.ask_question(chat_id, question)
            return result
        except Exception as e:
            logger.error(
                "An error occurred while asking the processor a question: %s", e
            )
            raise

    def process_endpoint_result(self, chat_id, script_result):
        # Validate input
        if not all([chat_id, script_result]):
            return HttpResponseBadRequest(
                json.dumps(
                    {"error": "Invalid input. chat_id and script_result are required."}
                ),
                content_type="application/json",
            )

        try:
            # Parse the JSON response
            endpoint_result_json = json.loads(script_result)

            # Check if the JSON response contains the 'operation' key
            if (
                "operation" in endpoint_result_json
                and endpoint_result_json["operation"] is not None
            ):
                # Process the endpoint result
                template = self.create_endpoint_template(endpoint_result_json)
                template = self.populate_endpoint_template(
                    endpoint_result_json, template
                )
                return JsonResponse(template, status=200)
            else:
                return JsonResponse({"answer": endpoint_result_json}, status=200)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from processor: %s", e)
            return HttpResponseServerError(
                json.dumps(
                    {"error": "Invalid JSON response from processor", "details": str(e)}
                ),
                content_type="application/json",
            )
        except Exception as e:
            logger.error(
                "An error occurred while processing the endpoint result: %s", e
            )
            return HttpResponseServerError(
                json.dumps(
                    {
                        "error": "An error occurred while processing the endpoint result.",
                        "details": str(e),
                    }
                ),
                content_type="application/json",
            )

    def create_endpoint_template(self, endpoint_result_json):
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

    def populate_endpoint_template(self, endpoint_result_json, template):
        if (
            "parameters" in endpoint_result_json
            and endpoint_result_json["parameters"] is not None
        ):
            res_params = endpoint_result_json["parameters"]
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
                    "template": "false",
                    "templateValue": "",
                    "excludeFromCacheKey": "false",
                    "type": "REQUEST_PARAM",
                    "optionValues": [],
                }
                for key in param_keys_to_check:
                    if key in res_param and res_param[key] is not None:
                        param_template[key] = res_param[key]
                param_template = self.process_endpoint_param(
                    template, res_param, param_template
                )
                logger.info("parameters==")
                logger.info(param_template)
                template["parameters"].append(param_template)
        logger.info("template==")
        logger.info(template)
        return template

    def process_endpoint_param(self, template, res_param, param_template):
        # Validate input
        if any(arg is None for arg in [template, res_param, param_template]):
            raise ValueError("Template, res_param, and param_template cannot be None")

        try:
            # Process the parameter based on the method type
            if template["method"] == "POST_BODY":
                param_template["type"] = "REQUEST_BODY_VARIABLE"
            elif template["method"] == "GET":
                if "in" in res_param and res_param["in"] is not None:
                    param_template["type"] = res_param["in"]
                else:
                    param_template["type"] = "REQUEST_PARAM"
            return param_template
        except Exception as e:
            logger.error("An error occurred while processing endpoint parameter: %s", e)
            raise
