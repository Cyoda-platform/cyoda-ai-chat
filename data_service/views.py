import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.interactor import TrinoInteractor
from .logic.prompts import RETURN_DATA
from .logic.processor import TrinoProcessor

logger = logging.getLogger("django")
interactor = TrinoInteractor(TrinoProcessor())


# Views
class InitialTrinoView(views.APIView):
    """View to handle initial trino requests."""

    def get(self, request):
        """Handle POST requests to initialize a trino."""
        try:
            logger.info("Starting InitialTrinoView")
            token = request.headers.get("Authorization")
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            schema_name = request.query_params.get("schema_name")
            if not schema_name:
                return Response(
                    {"error": "schema_name is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.initialize_chat(token, chat_id, schema_name)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error initializing trino: %s", e)
            return Response(
                {"error": "Failed to initialize trino"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatTrinoView(views.APIView):
    """View to handle chat mapping requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat trino."""
        logger.info("Starting ChatTrinoView")
        try:
            token = request.headers.get("Authorization")
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.chat(token, chat_id, request.data, None, None)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing trino chat: %s", e)
            return Response(
                {"error": "Failed to process trino chat request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatTrinoClearView(views.APIView):
    """View to handle chat trino clear requests."""

    def get(self, request):
        """Handle GET requests to clear a chat trino."""
        logger.info("Starting ChatTrinoClearView")
        try:
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            token = request.headers.get("Authorization")
            response = interactor.clear_chat(chat_id, token)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error clearing trino chat: %s", e)
            return Response(
                {"error": "Failed to clean trino chat"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatTrinoRunQueryView(views.APIView):
    """View to handle chat mapping requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat trino."""
        logger.info("Starting ChatTrinoView")
        try:
            response = interactor.run_query(request.data["query"])
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing trino chat: %s", e)
            return Response(
                {"error": "Failed to process trino chat request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ChatTrinoSaveView(views.APIView):

    def post(self, request, *args, **kwargs):
        logger.info("Starting ChatTrinoSaveView")
        try:
            token = request.headers.get("Authorization")
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            interactor.update_chat_id(token, chat_id)
            return Response({"success": f"{chat_id}"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error processing trino chat: %s", e)
            return Response(
                {"error": "Failed to process trino chat request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ReturnDataView(views.APIView):
    """
    View to handle requests to return data.
    """

    def get(self, request):
        """
        Handle GET requests to return data.
        """
        return_data = RETURN_DATA
        logger.info("Returning data")
        return Response(return_data, status=status.HTTP_200_OK)
