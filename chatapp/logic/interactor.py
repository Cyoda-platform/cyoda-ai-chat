import json
import logging
from .processor import EDMProcessor
from . import prompts
from rest_framework.response import Response
from rest_framework import status

processor = EDMProcessor()
logging.basicConfig(level=logging.INFO)

initialized_columns=set()
initialized_script =set()

class MappingsInteractor:
    def __init__(self):
        logging.info("Initializing...")
    
    def initialize_mapping(self, chat_id, ds_input, entity):
        # Use a try-except block to handle errors gracefully
        try:

            question = (prompts.MAPPINGS_INITIAL_PROMPT).format(ds_input, entity, entity)
            result = processor.ask_question(chat_id, question)
            logging.info(result)

            return Response({"answer":"initialization complete"}, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle any exceptions that may occur during processing
            logging.error("An error occurred: %s", e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def initialize_script(self, chat_id):
    # Use a try-except block to handle errors gracefully
        if chat_id not in initialized_script:
            try:
                question = prompts.MAPPINGS_INITIAL_PROMPT_SCRIPT
                result = processor.ask_question(chat_id, question)
                logging.info(result)
                initialized_script.add(chat_id)

                return Response({"answer":"script initialization complete"}, status=status.HTTP_200_OK)

            except Exception as e:
                # Handle any exceptions that may occur during processing
                logging.error("An error occurred: %s", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def initialize_columns(self, chat_id):
    # Use a try-except block to handle errors gracefully
        if chat_id not in initialized_columns:
            try:
                question = prompts.MAPPINGS_INITIAL_PROMPT_COLUMNS
                result = processor.ask_question(chat_id, question)
                logging.info(result)
                initialized_columns.add(chat_id)

                return Response({"answer":"columns initialization complete"}, status=status.HTTP_200_OK)

            except Exception as e:
                # Handle any exceptions that may occur during processing
                logging.error("An error occurred: %s", e)
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def clear_context(self, chat_id):
        processor.chat_history.clear_chat_history(chat_id)
        if chat_id in initialized_columns:
            initialized_columns.remove(chat_id)
        if chat_id in initialized_script:
            initialized_script.remove(chat_id)
        return Response(
            {"message": f"Chat mapping with id {chat_id} cleared."},
            status=status.HTTP_200_OK,
        )


    def chat(self, chat_id, user_script, return_object, question):
        # Initialize current_script and return_string
        self.initialize_return_object(chat_id, return_object)
        current_script = f"Current script: {user_script}." if user_script else ""
        return_string = prompts.RETURN_DATA.get(return_object, "")
        # Construct ai_question
        ai_question = f"{question}. {current_script} {return_string}"
        logging.info(ai_question)
        # Ask question to processor
        result = processor.ask_question(chat_id, ai_question)
        # Handle different return_objects
        return self.process_return_object(chat_id, return_object, result)

    def initialize_return_object(self, chat_id, return_object):
        if return_object == "script":
            self.initialize_script(chat_id)
        #elif return_object == "columns":
        #    self.initialize_columns(chat_id)

    def process_return_object(self, chat_id, return_object, result):
        if return_object in ["random", "code", "autocomplete"]:
            response_data = {"answer": result}
        elif return_object == "script":
            response_data = self.process_script_return(chat_id, result)
        elif return_object == "transformers":
            response_data = self.process_transformers(result)
        elif return_object == "columns":
            try:
                result_dict = json.loads(result)
                response_data = result_dict
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

