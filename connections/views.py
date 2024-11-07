import logging
from rest_framework import status, views
from rest_framework.response import Response
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from .logic.interactor import ConnectionsInteractor, chat_id_prefix
from .logic.ingestion_service import DataIngestionService
from .logic.prompts import RETURN_DATA
from .logic.processor import ConnectionProcessor
from config_generator import config_view_functions

logger = logging.getLogger("django")

interactor = ConnectionsInteractor(ConnectionProcessor())
ingestionService = DataIngestionService()
ERROR_PROCESSING_REQUEST_MESSAGE = "Error processing chat connection request"

class InitialConnectionView(views.APIView):

    def post(self, request, *args, **kwargs):
        return config_view_functions.initial(request, interactor, chat_id_prefix)


class ChatConnectionInitializedView(views.APIView):

    def get(self, request):
        return config_view_functions.is_initialized(request, interactor, chat_id_prefix)


class ChatConnectionView(views.APIView):

    def post(self, request, *args, **kwargs):
        return config_view_functions.chat(request, interactor, chat_id_prefix)

#todo get-> put
class ChatConnectionClearView(views.APIView):

    def get(self, request):
        return config_view_functions.chat_clear(request, interactor, chat_id_prefix)

class ChatSaveChatView(views.APIView):

    def get(self, request):
        return config_view_functions.write_back_chat_cache(request, interactor, chat_id_prefix)

class ChatConnectionGetUserChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_user_chat_history(request, interactor, chat_id_prefix)

class ReturnDataView(views.APIView):

    def get(self, request):
        return config_view_functions.return_data(RETURN_DATA)


class ChatConnectionUpdateIdView(views.APIView):

    def put(self, request, *args, **kwargs):
        return config_view_functions.update_id(request, interactor, chat_id_prefix)


class ChatConnectionGetChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_history(request, interactor, chat_id_prefix)


class ChatIngestDataView(views.APIView):

    def get(self, request):

        print(request.query_params.get("datasource_id", ""))
        try:
            token = request.headers.get("Authorization")
            if not token:
                return Response(
                    {"success": False, "message": "Authorization header is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            request_data = {
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
                {"success": False, "message": "Invalid input. Please check the request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ObjectDoesNotExist as e:
            logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: {e}")
            return Response(
                {"success": False, "message": "Object not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: {e}")
            logger.exception("An exception occurred")
            return Response(
                {"success": False, "message": f"Error processing chat workflow: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
