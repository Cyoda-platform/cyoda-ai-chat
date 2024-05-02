import json
import logging
from .processor import ConnectionProcessor
from . import prompts
from rest_framework.response import Response
from rest_framework import status

processor = ConnectionProcessor()
logging.basicConfig(level=logging.INFO)
initialized_requests = set()


class ConnectionsInteractor:
    def __init__(self):
        logging.info("Initializing...")

    def initialize_connection(self, chat_id, ds_doc):
        # Use a try-except block to handle errors gracefully
        try:
            # Return a successful response with the template
            return Response("pass", status=status.HTTP_200_OK)

        except Exception as e:
            # Handle any exceptions that may occur during processing
            logging.error("An error occurred: %s", e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def clear_context(self, chat_id):
        processor.chat_history.clear_chat_history(chat_id)
        if chat_id in initialized_requests:
            initialized_requests.remove(chat_id)
            return Response(
                {"message": f"Chat mapping with id {chat_id} cleared."},
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "message": f"Chat mapping with id {chat_id} has not beed initialized yet."
            },
            status=status.HTTP_200_OK,
        )

    def chat(self, chat_id, user_endpoint, return_object, question):
        # Initialize current_script and return_string
        if chat_id not in initialized_requests:
            if return_object != "endpoints":
                return Response(
                    {"answer": "Please, initialize the endpoints request first."},
                    status=status.HTTP_200_OK,
                )
            initialized_requests.add(chat_id)
            resp = self.initialize_connection_request(chat_id, question)
            return Response(resp, status=status.HTTP_200_OK)

        return_string = prompts.RETURN_DATA.get(return_object, "")
        # Construct ai_question
        current_endpoint = (
            f"Current endpoint: {user_endpoint}." if user_endpoint else ""
        )
        ai_question = f"{question}. {current_endpoint} \n {return_string}"
        logging.info(ai_question)
        # Ask question to processor
        result = processor.ask_question(chat_id, ai_question)
        # Handle different return_objects
        if return_object == "random":
            resp = {"answer": result}
            logging.info(resp)
            return Response(resp, status=status.HTTP_200_OK)
        elif return_object == "endpoints":
            resp = self.process_endpoint_result(chat_id, result)
            logging.info(resp)
            return Response(resp, status=status.HTTP_200_OK)
        # json response
        else:
            try:
                result_dict = json.loads(result)
                return Response(result_dict, status=status.HTTP_200_OK)
            except json.JSONDecodeError as e:
                logging.error("Invalid JSON response from processor %s", e)
                return Response(
                    {
                        "error": "Invalid JSON response from processor",
                        "details": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

    def initialize_connection_request(self, chat_id, question):
        init_request_question = (prompts.INITIAL_REQUEST_ANALYSIS_PROMPT).format(
            question
        )
        result = processor.ask_question(chat_id, init_request_question)
        logging.info(result)
        init_params_question = (prompts.INITIAL_PARAMETERS_ANALYSIS_PROMPT).format(
            question
        )
        result = processor.ask_question(chat_id, init_params_question)
        logging.info(result)
        init_question = (
            (prompts.INITIAL_API_PROMPT).format(question)
            + " "
            + prompts.RETURN_DATA.get("endpoints")
        )
        result = processor.ask_question(chat_id, init_question)
        resp = self.process_endpoint_result(chat_id, result)
        logging.info(resp)
        return resp

    def process_endpoint_result(self, chat_id, script_result):
        try:
            endpoint_result_json = json.loads(script_result)
            if (
                "operation" in endpoint_result_json
                and endpoint_result_json["operation"] is not None
            ):
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
                    if (
                        key in endpoint_result_json
                        and endpoint_result_json[key] is not None
                    ):
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
                        logging.info("parameters==")
                        logging.info(param_template)
                        template["parameters"].append(param_template)
                logging.info("template==")
                logging.info(template)
                return template
            else:
                return {"answer": endpoint_result_json}

        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
        return {"answer": endpoint_result_json}

    def process_endpoint_param(self, template, res_param, param_template):
        # Define constants for method types
        POST_BODY = "POST_BODY"
        REQUEST_BODY_VARIABLE = "REQUEST_BODY_VARIABLE"
        REQUEST_PARAM = "REQUEST_PARAM"

        # Check if template and param_template are not None
        if template is None or param_template is None:
            raise ValueError("Template or param_template cannot be None")

        # Process POST_BODY method
        if template["method"] == POST_BODY:
            if (
                param_template["type"] is not None
                and param_template["type"] != REQUEST_BODY_VARIABLE
            ):
                param_template["type"] = REQUEST_BODY_VARIABLE
            elif param_template["type"] is None:
                param_template["type"] = REQUEST_BODY_VARIABLE

        # Process GET method
        elif template["method"] == "GET":
            if param_template["type"] is None and res_param["in"] is not None:
                param_template["type"] = res_param["in"]
            elif param_template["type"] is None:
                param_template["type"] = REQUEST_PARAM
        return param_template
