import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.interactor import TrinoInteractor

logger = logging.getLogger("django")
interactor = TrinoInteractor()


# Views
class InitialTrinoView(views.APIView):
    """View to handle initial trino requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to initialize a trino."""
        try:
            logger.info("Starting InitialTrinoView")
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.initialize(chat_id)
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
            chat_id = request.query_params.get("chat_id")
            if not chat_id:
                return Response(
                    {"error": "chat_id is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            response = interactor.chat(chat_id, request.data)
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
            response = interactor.clear_context(chat_id)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error clearing trino chat: %s", e)
            return Response(
                {"error": "Failed to clean trino chat"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
