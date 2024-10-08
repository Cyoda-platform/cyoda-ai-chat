import logging
from rest_framework import status, views
from rest_framework.response import Response
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from .logic.dto import (
    InitialConnectionRequestDTO,
    ChatConnectionRequestDTO,
)
from .logic.serializers import InitialConnectionSerializer, ChatConnectionSerializer
from .logic.interactor import ConnectionsInteractor
from .logic.ingestion_service import DataIngestionService
from .logic.prompts import RETURN_DATA
from .logic.processor import ConnectionProcessor

logger = logging.getLogger("django")

interactor = ConnectionsInteractor(ConnectionProcessor())
ingestionService = DataIngestionService()
ERROR_PROCESSING_REQUEST_MESSAGE = "Error processing chat connection request"


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
            initial_connection_request = InitialConnectionRequestDTO(
                **serializer.validated_data
            )
            try:
                response = interactor.initialize_connection(
                    initial_connection_request.id,
                    initial_connection_request.ds_doc,
                )
                logger.info(
                    "Initial connection established for chat_id: %s",
                    initial_connection_request.id,
                )
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error initializing connection: %s", e)
                return Response(
                    {"error": "Failed to initialize connection"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
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
            chat_connection_request = ChatConnectionRequestDTO(
                **serializer.validated_data
            )
            try:
                token = request.headers.get("Authorization")
                response = interactor.chat(
                    token,
                    chat_connection_request.id,
                    chat_connection_request.return_object,
                    chat_connection_request.question,
                )
                logger.info(
                    "Chat connection request processed for chat_id: %s",
                    chat_connection_request.id,
                )
                return Response(response, status=status.HTTP_200_OK)
            except BadRequest as e:
                logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
                return Response(
                    {"error": "Invalid input. Please check the request."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except ObjectDoesNotExist as e:
                logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
                return Response(
                    {"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
                return Response(
                    {"error": "Failed to process chat connection request"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.warning(
                "Invalid data for chat connection request: %s", serializer.errors
            )
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
            return Response(
                {"error": "Failed to clear context"},
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


class ChatIngestDataView(views.APIView):
    """
    View to handle chat connection requests.
    """

    def get(self, request):
        """
        Handle POST requests to process a chat connection.
        """
        print(request.query_params.get("datasource_id", ""))
        try:
            token = request.headers.get("Authorization")
            if not token:
                return Response(
                    {"error": "Authorization header is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request_data={
                "ds_id": request.query_params.get("datasource_id"),
                "operation": request.query_params.get("operation"),
                "schema_flag": request.query_params.get("schema") == "true",
                "data_format": request.query_params.get("dataFormat"),
                "entity_name": request.query_params.get("entityName"),
                "model_version": request.query_params.get("modelVersion"),
                "entity_type": request.query_params.get("entityType")
            }
            ingestionService.ingest_data(token, request_data)

            return Response({"success": True}, status=status.HTTP_200_OK)
        except BadRequest as e:
            logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: {e}")
            return Response(
                {"error": "Invalid input. Please check the request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ObjectDoesNotExist as e:
            logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: {e}")
            return Response(
                {"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: {e}")
            return Response(
                {"error": "Failed to process chat connection request"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )