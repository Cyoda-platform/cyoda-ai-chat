import json
import logging
from .processor import EDMProcessor
from . import prompts
from rest_framework.response import Response
from rest_framework import status

processor = EDMProcessor()
logging.basicConfig(level=logging.INFO)


class MappingsInteractor:
    def __init__(self):
        logging.info("Initializing...")
    def get_response_mapping(self, result_json_string):
        try:
            result_dict = json.loads(result_json_string)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON response from processor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create a copy of the response template
        response_template_copy = prompts.RESPONSE_TEMPLATE.copy()

        # Check if the result_dict is a list before extending
        if isinstance(result_dict, list):
            response_template_copy["entityMappings"][0]["columns"].extend(result_dict)
        else:
            return Response(
                {"error": "The response from the processor is not a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response_template_copy


    def initialize_mapping(self, chat_id, ds_input, entity):
        # Use a try-except block to handle errors gracefully
        try:
            # Define the question to be asked
            question = (prompts.MAPPINGS_INITIAL_PROMPT).format(ds_input, entity)

            # Log the question and process it
            logging.info(question)
            result_json_string = processor.ask_question(chat_id, question)

            # Get the response template from the result
            response_template = self.get_response_mapping(result_json_string)

            # Return a successful response with the template
            return Response(response_template, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle any exceptions that may occur during processing
            logging.error("An error occurred: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def generate_script(self, chat_id):
        question = prompts.SCRIPT_GEN_PROMPT
        logging.info(question)
        script_result = processor.ask_question(chat_id, question)
        try:
            script_result_json = json.loads(script_result)
            if "script" in script_result_json and script_result_json["script"] is not None:
                return Response(script_result_json, status=status.HTTP_200_OK)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)

        refine_question = prompts.SCRIPT_REFINE_PROMPT
        refine_result = processor.ask_question(chat_id, refine_question)
        logging.info(refine_result)
        try:
            input_src_paths = json.loads(refine_result)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor 2: %s", e)
            return Response(
                {
                    "error": "Invalid JSON response from processor",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        script = {"script": {"body": script_result, "inputSrcPaths": input_src_paths}}
        return Response(script, status=status.HTTP_200_OK)


    def clear_context(self, chat_id):
        processor.chat_history.clear_chat_history(chat_id)
        return Response(
            {"message": f"Chat mapping with id {chat_id} cleared."},
            status=status.HTTP_200_OK,
        )


    def chat(self, chat_id, user_script, return_object, question):
        # Initialize current_script and return_string
        current_script = f"Current script: {user_script}." if user_script else ""
        return_string = prompts.RETURN_DATA.get(return_object, "")
        # Construct ai_question
        ai_question = f"{question}. {current_script} {return_string}"
        logging.info(ai_question)
        # Ask question to processor
        result = processor.ask_question(chat_id, ai_question)
        # Handle different return_objects
        if return_object in ["random", "code", "autocomplete"]:
            response_data = {"answer": result}
            return Response(response_data, status=status.HTTP_200_OK)
        elif return_object == "mapping":
            response_template = self.get_response_mapping(result)
            return Response(response_template, status=status.HTTP_200_OK)
        elif return_object == "script":
            resp = self.process_script_return(chat_id, result)
            logging.info(resp)
            return Response(resp, status=status.HTTP_200_OK)      
        elif return_object == "transformers":
            resp = self.process_transformers(result)
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
    def process_script_return(self, chat_id, script_result):
        try:
            script_result_json = json.loads(script_result)
            if "script" in script_result_json and script_result_json["script"] is not None:
                logging.info("script included")
                return script_result_json
            elif "body" in script_result_json and script_result_json["body"] is not None:
                logging.info("body included")
                if "inputSrcPaths" in script_result_json and script_result_json["inputSrcPaths"] is not None:
                   logging.info("inputSrcPaths included")
                   script = {"script": {"body": script_result_json["body"], "inputSrcPaths": script_result_json["inputSrcPaths"]}}
                   logging.info(script)
                   return script
                else:
                    input_src_paths = self.get_input_scr_params(chat_id)
                    script = {"script": script_result_json, "inputSrcPaths": input_src_paths}
                    return script

        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
        logging.info("only code included")
        input_src_paths = self.get_input_scr_params(chat_id)
        logging.info(input_src_paths)
        script = {"script": {"body": script_result, "inputSrcPaths": input_src_paths}}
        return script
    
    def get_input_scr_params(self, chat_id):
        refine_question = prompts.SCRIPT_REFINE_PROMPT
        refine_result = processor.ask_question(chat_id, refine_question)
        logging.info(refine_result)
        try:
            input_src_paths = json.loads(refine_result)
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor: %s", e)
            raise
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

