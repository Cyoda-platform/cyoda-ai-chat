import json
import logging
from .processor import ConnectionProcessor
from . import prompts
from rest_framework.response import Response
from rest_framework import status

processor = ConnectionProcessor()
logging.basicConfig(level=logging.INFO)


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
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def clear_context(self, chat_id):
        processor.chat_history.clear_chat_history(chat_id)
        return Response(
            {"message": f"Chat mapping with id {chat_id} cleared."},
            status=status.HTTP_200_OK,
        )


    def chat(self, chat_id, user_endpoint, return_object, question):
        # Initialize current_script and return_string
        return_string = prompts.RETURN_DATA.get(return_object, "")
        # Construct ai_question
        current_endpoint = f"Current endpoint: {user_endpoint}." if user_endpoint else ""
        ai_question = f"{question}. {current_endpoint} \n {return_string}"
        logging.info(ai_question)
        # Ask question to processor
        result = processor.ask_question(chat_id, ai_question)
        # Handle different return_objects
        if return_object == "endpoints":
            resp = self.process_endpoint_result(chat_id, result)
            logging.info(resp)
            return Response(resp, status=status.HTTP_200_OK)
        #json response
        else:
            try:
                result_dict = json.loads(result)
                return Response(result_dict, status=status.HTTP_200_OK)
            except json.JSONDecodeError as e:
                logging.error("Invalid JSON response from processor %s", e)
                return Response(
                    {"error": "Invalid JSON response from processor", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
                
    def process_endpoint_result(self, chat_id, script_result):
        try:
            endpoint_result_json = json.loads(script_result)
            if "operation" in endpoint_result_json and endpoint_result_json["operation"] is not None:
                logging.info("operation included")
                template = prompts.RESPONSE_TEMPLATE.copy()
                template["operation"]=endpoint_result_json["operation"]
                template["query"]=endpoint_result_json["query"]
                template["method"]=endpoint_result_json["method"]
                template["parameters"]=endpoint_result_json["parameters"]
                template["bodyTemplate"]=endpoint_result_json["bodyTemplate"]
                template["connectionTimeout"]=endpoint_result_json["connectionTimeout"]
                template["readWriteTimeout"]=endpoint_result_json["readWriteTimeout"]
                return template
            else:
                return {"answer": endpoint_result_json}

        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
        return {"answer": endpoint_result_json}
    
