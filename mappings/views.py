import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.prompts import RETURN_DATA
from .logic.dto import InitialMappingRequestDTO, ChatMappingRequestDTO
from .logic.serializers import InitialMappingSerializer, ChatMappingSerializer
from .logic.interactor import MappingsInteractor


logger = logging.getLogger(__name__)
interactor = MappingsInteractor()

# Views
class InitialMappingView(views.APIView):
    """View to handle initial mapping requests."""
    def post(self, request, *args, **kwargs):
        """Handle POST requests to initialize a mapping."""
        serializer = InitialMappingSerializer(data=request.data)
        if serializer.is_valid():
            initial_mapping_request = InitialMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                entity=serializer.validated_data.get("entity", ""),
                ds_input=serializer.validated_data.get("input", ""),
            )
            try:
                response = interactor.initialize_mapping(
                    initial_mapping_request.chat_id,
                    initial_mapping_request.entity,
                    initial_mapping_request.ds_input
                )
                logger.info("Initial mapping request processed for chat_id: %s", initial_mapping_request.chat_id)
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error processing initial mapping request: %s", e)
                return Response({"error": "Failed to process initial mapping request"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("Invalid data for initial mapping request: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatMappingView(views.APIView):
    """View to handle chat mapping requests."""
    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat mapping."""
        serializer = ChatMappingSerializer(data=request.data)
        if serializer.is_valid():
            chat_mapping_request = ChatMappingRequestDTO(
                chat_id=serializer.validated_data.get("id", ""),
                question=serializer.validated_data.get("question", ""),
                user_script=serializer.validated_data.get("user_script", ""),
                return_object=serializer.validated_data.get("return_object", ""),
            )
            try:
                response = interactor.chat(
                    chat_mapping_request.chat_id,
                    chat_mapping_request.user_script,
                    chat_mapping_request.return_object,
                    chat_mapping_request.question
                )
                logger.info("Chat mapping request processed for chat_id: %s", chat_mapping_request.chat_id)
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                logger.error("Error processing chat mapping request: %s", e)
                return Response({"error": "Failed to process chat mapping request"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("Invalid data for chat mapping request: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChatMappingClearView(views.APIView):
    """View to handle chat mapping clear requests."""
    def get(self, request):
        """Handle GET requests to clear a chat mapping."""
        chat_id = request.query_params.get("id", "")
        try:
            interactor.clear_context(chat_id)
            logger.info("Context cleared for chat_id: %s", chat_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error("Error clearing context: %s", e)
            return Response({"error": "Failed to clear context"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReturnDataView(views.APIView):
    """View to handle requests to return data."""
    def get(self, request):
        """Handle GET requests to return data."""
        return_data = RETURN_DATA
        logger.info("Returning data")
        return Response(return_data, status=status.HTTP_200_OK)