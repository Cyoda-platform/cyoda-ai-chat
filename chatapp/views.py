import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.prompts import RETURN_DATA
from .logic.dto import InitialMappingRequestDTO, ChatMappingRequestDTO
from .logic.serializers import MessageSerializer
from .logic.interactor import MappingsInteractor


logging.basicConfig(level=logging.INFO)
interactor = MappingsInteractor()

class InitialMappingView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            initial_mapping_request = InitialMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                entity=serializer.validated_data.get("entity", ""),
                ds_input=serializer.validated_data.get("input", ""),
            )
            response = interactor.initialize_mapping(initial_mapping_request.chat_id, initial_mapping_request.entity, initial_mapping_request.ds_input)
            return response

class ScriptMappingView(views.APIView):
    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        return interactor.generate_script(chat_id)


class ChatMappingClearView(views.APIView):
    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        return interactor.clear_context(chat_id)


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
            return interactor.chat(chat_mapping_request.chat_id, chat_mapping_request.user_script, chat_mapping_request.return_object, chat_mapping_request.question)

class ReturnDataView(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(RETURN_DATA, status=status.HTTP_200_OK)
