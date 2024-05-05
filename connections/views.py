"""
This module contains the views for handling various connections and
data retrieval in a Django application.

Classes:
- InitialConnectionView: Handles initial connection requests.
- ChatConnectionClearView: Clears chat connections.
- ChatConnectionView: Handles chat connection requests.
- ReturnDataView: Returns data.

Each view class has a `post` method for handling POST requests
and a `get` method for handling GET requests.

Module Dependencies:
- logging
- Django's HttpResponse, JsonResponse, and HttpResponseServerError
- Django's View and method_decorator
- Django's csrf_exempt decorator
- MessageSerializer from .logic.serializers
- ConnectionsInteractor from .logic.interactor
- InitialConnectionRequestDTO and ChatConnectionRequestDTO from .logic.dto
- RETURN_DATA from .logic.prompts

Note: The views are decorated with csrf_exempt to allow for cross-site request forgery. 
This should be handled properly in a production environment.
"""

import logging
from rest_framework import status, views
from rest_framework.response import Response
from .logic.dto import InitialConnectionRequestDTO, ChatConnectionRequestDTO
from .logic.serializers import InitialConnectionSerializer, ChatConnectionSerializer
from .logic.interactor import ConnectionsInteractor
from .logic.prompts import RETURN_DATA

logger = logging.getLogger(__name__)
interactor = ConnectionsInteractor()

class InitialConnectionView(views.APIView):
    """
    View to handle initial connection requests.
    """
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to initialize a connection.
        """
        serializer = InitialConnectionSerializer(data=request.data)
        if serializer.is_valid():
            initial_connection_request = InitialConnectionRequestDTO(**serializer.validated_data)
            try:
                response = interactor.initialize_connection(
                    initial_connection_request.chat_id,
                    initial_connection_request.ds_doc,
                )
                logger.info("Initial connection established for chat_id: %s", initial_connection_request.chat_id)
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error initializing connection: %s", e)
                return Response({"error": "Failed to initialize connection"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("Invalid data for initial connection: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatConnectionView(views.APIView):
    """
    View to handle chat connection requests.
    """
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to process a chat connection.
        """
        serializer = ChatConnectionSerializer(data=request.data)
        if serializer.is_valid():
            chat_connection_request = ChatConnectionRequestDTO(**serializer.validated_data)
            try:
                response = interactor.chat(
                    chat_connection_request.chat_id,
                    chat_connection_request.user_endpoint,
                    chat_connection_request.return_object,
                    chat_connection_request.question,
                )
                logger.info("Chat connection request processed for chat_id: %s", chat_connection_request.chat_id)
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error processing chat connection request: %s", e)
                return Response({"error": "Failed to process chat connection request"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("Invalid data for chat connection request: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatConnectionClearView(views.APIView):
    """
    View to handle chat connection clear requests.
    """
    def get(self, request):
        """
        Handle GET requests to clear a chat connection.
        """
        chat_id = request.query_params.get("id", "")
        try:
            interactor.clear_context(chat_id)
            logger.info("Context cleared for chat_id: %s", chat_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error("Error clearing context: %s", e)
            return Response({"error": "Failed to clear context"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
