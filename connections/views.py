import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.prompts import RETURN_DATA
from .logic.dto import InitialConnectionRequestDTO, ChatMappingRequestDTO
from .logic.serializers import MessageSerializer
from .logic.interactor import ConnectionsInteractor


logging.basicConfig(level=logging.INFO)
interactor = ConnectionsInteractor()

class InitialConnectionView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            initial_connection_request = InitialConnectionRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                ds_doc=serializer.validated_data.get("ds_doc", ""),
            )
            response = interactor.initialize_connection(initial_connection_request.chat_id, initial_connection_request.ds_doc)
            return response

class ChatMappingClearView(views.APIView):
    def get(self, request, *args, **kwargs):
        chat_id = request.query_params.get("id", "")
        return interactor.clear_context(chat_id)


class ChatMappingView(views.APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            chat_connection_request = ChatMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                question=serializer.validated_data.get("question", ""),
                user_endpoint=serializer.validated_data.get("user_endpoint", ""),
                return_object=serializer.validated_data.get("return_object", ""),
            )
            return interactor.chat(chat_connection_request.chat_id, chat_connection_request.user_endpoint, chat_connection_request.return_object, chat_connection_request.question)

class ReturnDataView(views.APIView):
    def get(self, request, *args, **kwargs):
        return Response(RETURN_DATA, status=status.HTTP_200_OK)
