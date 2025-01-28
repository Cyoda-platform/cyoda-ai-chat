import logging

from rest_framework.response import Response
from rest_framework import status, views

from common_utils.utils import get_user_answer
from .logic import prompts
from .logic.interactor import WorkflowsInteractor, chat_id_prefix
from .logic.prompts import RETURN_DATA
from .logic.processor import WorkflowProcessor
from .logic.workflow_gen_service import WorkflowGenerationService
from config_generator import config_view_functions

logger = logging.getLogger('django')
interactor = WorkflowsInteractor(WorkflowProcessor(), WorkflowGenerationService())


class InitialWorkflowView(views.APIView):

    def post(self, request, *args, **kwargs):
        return config_view_functions.initial(request, interactor, chat_id_prefix)

class ChatWorkflowInitializedView(views.APIView):

    def get(self, request):
        return config_view_functions.is_initialized(request, interactor, chat_id_prefix)

class ChatWorkflowView(views.APIView):

    def post(self, request, *args, **kwargs):
        try:
            token = request.headers.get("Authorization")
            if not token:
                return Response(
                    {"success": False, "message": "Authorization header is missing"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info("Starting ChatworkflowView")

            json_data = interactor.parse_request_data(request)
            chat_id = chat_id_prefix + json_data.get("chat_id")
            if not chat_id:
                return {"success": False, "message": "chat_id is missing"}

            return_object = json_data.get("return_object")
            if not return_object:
                return {"success": False, "message": "return_object is missing"}

            question = json_data.get("question")

            response = interactor.chat(token, chat_id, question, return_object, json_data)
            answer = get_user_answer(response)
            interactor.add_user_chat_hitory(token, chat_id, question, answer, return_object)
            ##todo need to improve here!
            if return_object in [prompts.Keys.GENERATE_WORKFLOW_FROM_URL.value, prompts.Keys.SAVE_WORKFLOW.value]:
                interactor.update_chat_id(token, chat_id, chat_id_prefix + answer.replace("Workflow id = ", ""))
            return Response(response)
        except Exception as e:
            logger.error(f"Error processing chat workflow: {e}")
            return Response({"success": False, "message": f"Error processing chat workflow: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatWorkflowClearView(views.APIView):

    def get(self, request):
        return config_view_functions.chat_clear(request, interactor, chat_id_prefix)

class ReturnDataView(views.APIView):

    def get(self, request):
        return config_view_functions.return_data(RETURN_DATA)


class ChatWorkflowUpdateIdView(views.APIView):
    def put(self, request, *args, **kwargs):
        return config_view_functions.update_id(request, interactor, chat_id_prefix)


class ChatWorkflowGetChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_history(request, interactor, chat_id_prefix)

class ChatSaveChatView(views.APIView):

    def get(self, request):
        return config_view_functions.write_back_chat_cache(request, interactor, chat_id_prefix)

class ChatWorkflowGetUserChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_user_chat_history(request, interactor, chat_id_prefix)


class GenerateWorkflowConfigView(views.APIView):

    def post(self, request, *args, **kwargs):
        logger.info("Starting GenerateWorkflowConfigView")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = chat_id_prefix + request.data.get("chat_id", "")
        if not chat_id:
            return Response(
                {"success": False, "message": "chat_id is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        class_name = request.data.get("class_name")
        if not class_name:
            return Response(
                {"success": False, "message": "class_name is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_data = interactor.save_workflow_entity(token, request.data, class_name)
        return Response(response_data)