import json
import logging

from rest_framework.response import Response
from rest_framework import status, views

from common_utils.utils import get_user_history_answer
from .logic.processor import MappingProcessor
from .logic.prompts import RETURN_DATA
from .logic.interactor import MappingsInteractor
from config_generator import config_view_functions

logger = logging.getLogger('django')
interactor = MappingsInteractor(MappingProcessor())
chat_id_prefix = "mappings"


class InitialMappingView(views.APIView):

    def post(self, request, *args, **kwargs):

        logger.info("Starting mapping initialization:")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = chat_id_prefix + request.data.get("chat_id")
        if not chat_id:
            return Response(
                {"success": False, "message": "chat_id is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ds_input = request.data.get("ds_input")
        entity_name = request.data.get("entity_name")
        if not (ds_input or entity_name):
            return Response(
                {"success": False, "message": "ds_input or entity_name is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            interactor.initialize_mapping(
                token,
                chat_id,
                ds_input,
                entity_name,
            )
            response = interactor.initialize_chat(token, chat_id, "None")

            logger.info(
                "Initial mapping request processed for chat_id: %s",
                chat_id,
            )
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing initial mapping request: %s", e)
            return Response(
                {"success": False, "message": f"Failed to process initial mapping request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatMappingInitializedView(views.APIView):

    def get(self, request):
        return config_view_functions.is_initialized(request, interactor, chat_id_prefix)


class ChatMappingView(views.APIView):

    def post(self, request, *args, **kwargs):
        try:
            token = request.headers.get("Authorization")
            if not token:
                return Response(
                    {"success": False, "message": "Authorization header is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            chat_id = chat_id_prefix + request.data.get("chat_id")
            if not chat_id:
                return Response(
                    {"success": False, "message": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            question = request.data.get("question")
            user_script = request.data.get("user_script")
            return_object = request.data.get("return_object")
            if not (question or user_script or return_object):
                return Response(
                    {"success": False, "message": "question or user_script or return_object is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.chat(
                token,
                chat_id,
                return_object,
                question,
                user_script
            )
            logger.info(
                "Chat mapping request processed for chat_id: %s",
                chat_id,
            )
            answer = get_user_history_answer(response)
            interactor.add_user_chat_hitory(token, chat_id, question, answer, return_object)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing chat mapping request: %s", e)
            return Response(
                {"success": False, "message": f"Failed to initialize connection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatMappingClearView(views.APIView):

    def get(self, request):
        return config_view_functions.chat_clear(request, interactor, chat_id_prefix)


class ReturnDataView(views.APIView):

    def get(self, request):
        return config_view_functions.return_data(RETURN_DATA)


class ChatMappingUpdateIdView(views.APIView):
    def put(self, request, *args, **kwargs):
        return config_view_functions.update_id(request, interactor, chat_id_prefix)


class ChatMappingGetChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_history(request, interactor, chat_id_prefix)

class ChatSaveChatView(views.APIView):

    def get(self, request):
        return config_view_functions.write_back_chat_cache(request, interactor, chat_id_prefix)

class ChatMappingGetUserChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_user_chat_history(request, interactor, chat_id_prefix)

