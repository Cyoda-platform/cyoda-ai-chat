import json
import logging
from rest_framework.response import Response
from rest_framework import status, views, serializers
from .logic.processor import EDMProcessor

processor = EDMProcessor()
logging.basicConfig(level=logging.INFO)
RETURN_DATA = {
    "mapping": "Return only json array of column mappings.",
    "script": "Return ONLY javascript nashorn script json object which contains body with javascript code and inputSrcPaths inside script attribute. Remove any leading text",
    "code": "Return javascript nashorn code only. Remove any leading text",
    "random": "",
    "autocomplete": "Return only the relevant code for autocomplete.",
    "columns": "Return only column mapping json object which contains srcColumnPath and etc inside \"column\" attribute. Add to this json one more attribute \"action\" with the value either add or delete depending on the question. Return inside an array"
}
#Write a script for notices. Return only the relevant code for autocomplete.

entity_dict = {}
input_dict = {}

class MessageSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    question = serializers.CharField(required=False)
    entity = serializers.CharField(required=False)
    input = serializers.CharField(required=False)
    return_object = serializers.CharField(required=False)
    user_script = serializers.CharField(required=False)
    content = serializers.CharField(required=False)  # Make this field optional


class InitialMappingRequestDTO:
    def __init__(self, chat_id, entity, ds_input):
        self.chat_id = chat_id
        self.entity = entity
        self.ds_input = ds_input

def get_response_mapping(result_json_string):
    response_template = {
                "@bean": "com.cyoda.plugins.mapping.core.dtos.DataMappingConfigDto",
                "id": "ef7bf900-00b3-11ef-b006-ba4744165259",
                "name": "test",
                "lastUpdated": 1713795828907,
                "dataType": "JSON",
                "description": "",
                "entityMappings": [
                    {
                        "id": {"id": "ef79fd30-00b3-11ef-b006-ba4744165259"},
                        "name": "test",
                        "entityClass": "net.cyoda.saas.model.TenderEntity",
                        "entityRelationConfigs": [{"srcRelativeRootPath": "root:/"}],
                        "columns": [],  # Initialize the columns list
                        "functionalMappings": [],
                        "columnPathsForUniqueCheck": [],
                        "metadata": [],
                        "cobiCoreMetadata": [],
                        "script": {},
                        "entityFilter": {
                            "@bean": "com.cyoda.core.conditions.GroupCondition",
                            "operator": "AND",
                            "conditions": [],
                        },
                    }
                ],
            }
    try:
        result_dict = json.loads(result_json_string)
    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid JSON response from processor"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    response_template["entityMappings"][0]["columns"].extend(result_dict)
    return response_template

class InitialMappingView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            initial_mapping_request = InitialMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                entity=serializer.validated_data.get("entity", ""),
                ds_input=serializer.validated_data.get("input", ""),
            )
            return_string = RETURN_DATA["mapping"]
            question = f"Produce a list of column mappings from input to this target entity. Input: {initial_mapping_request.ds_input}. Target Entity: {initial_mapping_request.entity}. Do NOT add mappings for lists or arrays. If a column is not present in net.cyoda.saas.model.TenderEntity remove it. Use slash for src Return json array of column mappings."
            logging.info(question)
            result_json_string = processor.ask_question(
                initial_mapping_request.chat_id, question
            )
            response_template = get_response_mapping(result_json_string)
            return Response(response_template, status=status.HTTP_200_OK)


class ScriptMappingView(views.APIView):

    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        question = f"Write a JavaScript Nashorn script to map the given input to the given entity. Use the instruction. Return only JavaScript Nashorn script."
        logging.info(question)
        result_json_string = processor.ask_question(chat_id, question)
        
        try:
            result_dict = json.loads(result_json_string)
            if "script" in result_dict and result_dict["script"] is not None:
                logging.info("RESULT IN SCRIPT")
                return Response(result_dict, status=status.HTTP_200_OK)           
        except json.JSONDecodeError as e:
            logging.error("Invalid JSON response from processor 1")
        
        refine_question = "Provide a list of inputSrcPaths for this script. Write correct inputSrcPaths with a forward slash and wildcard if applicable. Return a json array."
        result_json_string2 = processor.ask_question(chat_id, refine_question)
        logging.info(result_json_string2)
        result_dict = {}
        try:
            result_dict = json.loads(result_json_string2)
                       
        except json.JSONDecodeError as e:
            # Log the error for debugging purposes
            logging.error("Invalid JSON response from processor %s", e)
            return Response(
                {
                    "error": "Invalid JSON response from processor",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
        script = {"script": {"body": result_json_string, "inputSrcPaths": result_dict}}
        return Response(script, status=status.HTTP_200_OK)


class ChatMappingClearView(views.APIView):

    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        processor.chat_history.clear_chat_history(chat_id)
        return Response(
            {"message": f"Chat mapping with id {chat_id} cleared."},
            status=status.HTTP_200_OK,
        )


class ChatMappingRequestDTO:
    def __init__(self, chat_id, question, user_script, return_object):
        self.chat_id = chat_id
        self.question = question
        self.user_script = user_script
        self.return_object = return_object


class ChatMappingView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            chat_mapping_request = ChatMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                question=serializer.validated_data.get("question", ""),
                user_script=serializer.validated_data.get("user_script", ""),
                return_object=serializer.validated_data.get("return_object", ""),
            )
            current_script = (
                f"Current script: {chat_mapping_request.user_script}."
                if chat_mapping_request.user_script
                else ""
            )
            return_string = RETURN_DATA[chat_mapping_request.return_object]
            ai_question = (
                f"{chat_mapping_request.question}. {current_script} {return_string}"
            )
            logging.info(ai_question)
            # first generate the mapping
            result = processor.ask_question(chat_mapping_request.chat_id, ai_question)
            if chat_mapping_request.return_object in ["random", "code", "autocomplete"]:
                # Create the response dictionary
                response_data = {"answer": result}
                # Return the response as JSON
                return Response(response_data, status=status.HTTP_200_OK)
            elif chat_mapping_request.return_object in ["mapping"]:
                response_template = get_response_mapping(result)
                return Response(response_template, status=status.HTTP_200_OK)
            try:
                result_dict = json.loads(result)
            except json.JSONDecodeError as e:
                # Log the error for debugging purposes
                logging.error("Invalid JSON response from processor %s", e)
                return Response(
                    {
                        "error": "Invalid JSON response from processor",
                        "details": str(e),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(result_dict, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReturnDataView(views.APIView):
    def get(self, request, *args, **kwargs):

        return Response(RETURN_DATA, status=status.HTTP_200_OK)
