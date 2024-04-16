import json
import logging
from rest_framework.response import Response
from rest_framework import status, views, serializers
from .logic.processor import EDMProcessor

processor = EDMProcessor()
logging.basicConfig(level=logging.INFO)
RETURN_DATA = {
    "mapping": "Return only DataMappingConfigDto json.",
    "script": "Return ONLY script json object which contains body and inputSrcPaths inside script attribute. Remove any leading text",
    "code": "Return javascript nashorn code only. Remove any leading text",
    "random": "",
    "columns": 'Return only column mapping json object which contains srcColumnPath and etc inside \"column\" attribute. Add to this json one more attribute \"action\" with the value either add or delete depending on the question.',
}


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
            question = f"Produce a mapping from this input to this target entity. Input: {initial_mapping_request.ds_input}. Entity: {initial_mapping_request.entity}. {return_string}. Work only with JSON attributes that are simple and not arrays. Do NOT use any atributes that are not present in schema. {return_string}"
            logging.info(question)
            # Assuming processor.ask_question returns a JSON string
            # first generate the mapping
            result_json_string = processor.ask_question(
                initial_mapping_request.chat_id, question
            )
            # second - refine the mapping

            # Convert the JSON string back to a Python dictionary
            try:
                result_dict = json.loads(result_json_string)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON response from processor"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(result_dict, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScriptMappingView(views.APIView):

    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        return_string = RETURN_DATA["script"]
        question = f"Produce a script for this mapping. {return_string}"
        logging.info(question)
        result_json_string = processor.ask_question(chat_id, question)

        # Convert the JSON string back to a Python dictionary
        try:
            result_dict = json.loads(result_json_string)
        except json.JSONDecodeError:
            return Response(
                {"error": "Invalid JSON response from processor"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result_dict, status=status.HTTP_200_OK)


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
            ai_question = f"{chat_mapping_request.question}. {current_script} {return_string}"
            logging.info(ai_question)
            # first generate the mapping
            result = processor.ask_question(id, ai_question)
            if chat_mapping_request.return_object in ["random","code"]:
                # Create the response dictionary
                response_data = {"answer": result}
                # Return the response as JSON
                return Response(response_data, status=status.HTTP_200_OK)
            try:
                result_dict = json.loads(result)
            except json.JSONDecodeError as e:
                # Log the error for debugging purposes
                logging.error("Invalid JSON response from processor %s", e)
                return Response(
                    {"error": "Invalid JSON response from processor", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(result_dict, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReturnDataView(views.APIView):
    def get(self, request, *args, **kwargs):

        return Response(RETURN_DATA, status=status.HTTP_200_OK)
