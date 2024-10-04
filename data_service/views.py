import logging

from rest_framework.response import Response
from rest_framework import status, views

from .logic.interactor import TrinoInteractor
from .logic.prompts import RETURN_DATA
from .logic.processor import TrinoProcessor
from config_generator import config_view_functions

logger = logging.getLogger("django")
interactor = TrinoInteractor(TrinoProcessor())
chat_id_prefix = "trino"


class InitialTrinoView(views.APIView):

    def post(self, request):
        try:
            logger.info("Starting InitialTrinoView")
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
            schema_name = request.data.get("schema_name")
            if not schema_name:
                return Response(
                    {"success": False, "message": "schema_name is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.initialize_chat(token, chat_id, schema_name)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error initializing trino: %s", e)
            return Response(
                {"success": False, "message": f"Failed to initialize connection: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatTrinoInitializedView(views.APIView):

    def get(self, request):
        return config_view_functions.is_initialized(request, interactor, chat_id_prefix)


class ChatTrinoView(views.APIView):

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat trino."""
        logger.info("Starting ChatTrinoView")
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
            response = interactor.chat(token, chat_id, request.data.get("question"), "None", "None")
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing trino chat: %s", e)
            return Response(
                {"success": False, "message": f"Error processing chat workflow: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatTrinoClearView(views.APIView):

    def get(self, request):
        return config_view_functions.chat_clear(request, interactor, chat_id_prefix)


class ChatTrinoRunQueryView(views.APIView):

    def post(self, request, *args, **kwargs):
        logger.info("Starting ChatTrinoView")
        try:
            response = interactor.run_query(request.data["query"])
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing trino chat: %s", e)
            return Response(
                {"success": False, "message": f"Error processing chat workflow: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReturnDataView(views.APIView):

    def get(self, request):
        return config_view_functions.return_data(interactor, RETURN_DATA)


class ChatTrinoUpdateIdView(views.APIView):
    def put(self, request, *args, **kwargs):
        return config_view_functions.update_id(request, interactor, chat_id_prefix)


class ChatTrinoGetChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_history(request, interactor, chat_id_prefix)
