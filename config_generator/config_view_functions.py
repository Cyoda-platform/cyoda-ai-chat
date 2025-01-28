import json
import logging

from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import BadRequest, ObjectDoesNotExist

from common_utils.utils import get_user_answer
from config_generator.config_interactor import ConfigInteractor

from connections.logic import prompts as connections_prompts

#set_debug(True)
#set_verbose(True)
logger = logging.getLogger("django")

ERROR_PROCESSING_REQUEST_MESSAGE = "Error processing chat connection request"

def is_initialized(request, interactor: ConfigInteractor, chat_id_prefix):
    try:
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = chat_id_prefix + request.query_params.get("chat_id", "")
        if not chat_id:
            return Response(
                {"success": False, "message": "chat_id is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_initialized = interactor.chat_initialized(token, chat_id)
        logger.info("Context cleared for chat_id: %s", chat_id)
        return Response(chat_initialized, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error is_initialized: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def initial(request, interactor: ConfigInteractor, chat_id_prefix):
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
        response = interactor.initialize_chat(
            token,
            chat_id,
            "None",
        )
        logger.info(
            "Initial connection established for chat_id: %s",
            request.data.get("chat_id"),
        )
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error initializing connection: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def chat(request, interactor: ConfigInteractor, chat_id_prefix):

    try:
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = chat_id_prefix + request.data.get("chat_id")
        return_object = request.data.get("return_object")
        question = request.data.get("question")

        if not (chat_id or return_object or question):
            return Response(
                {"success": False, "message": "request parameter is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_file = request.FILES.get("file", None)
        response = interactor.chat(
            token=token,
            chat_id=chat_id,
            question=question,
            return_object=return_object,
            user_data="",
            user_file=user_file
        )
        logger.info(
            "Chat connection request processed for chat_id: %s", chat_id
        )
        answer = get_user_answer(response)
        interactor.add_user_chat_hitory(token, chat_id, question, answer, return_object)
        ##todo need to improve here!
        if (return_object in [connections_prompts.Keys.IMPORT_CONNECTION.value]):
            interactor.update_chat_id(token, chat_id, chat_id_prefix + json.loads(answer)["datasource_id"])
        return Response(response, status=status.HTTP_200_OK)
    except BadRequest as e:
        logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
        return Response(
            {"success": False, "message": "Invalid input. Please check the request."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except ObjectDoesNotExist as e:
        logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
        return Response(
            {"error": "Object not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def chat_clear(request, interactor: ConfigInteractor, chat_id_prefix):
    token = request.headers.get("Authorization")
    if not token:
        return Response(
            {"success": False, "message": "Authorization header is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    chat_id = chat_id_prefix + request.query_params.get("chat_id", "")
    if not chat_id:
        return Response(
            {"success": False, "message": "request parameter is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        interactor.clear_chat(token, chat_id)
        logger.info("Context cleared for chat_id: %s", chat_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error("Error chat_clear: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def return_data(return_data):
    logger.info("Returning data")
    return Response(return_data, status=status.HTTP_200_OK)


def update_id(request, interactor: ConfigInteractor, chat_id_prefix):
    try:
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        init_chat_id = chat_id_prefix + request.data.get("init_chat_id")
        update_chat_id = chat_id_prefix + request.data.get("update_chat_id")
        if not (init_chat_id or update_chat_id):
            return Response(
                {"success": False, "message": "request parameter is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = interactor.update_chat_id(token, init_chat_id, update_chat_id)
        logger.info(
            "Chat connection request processed for init_chat_id: %s, update_chat_id: %s",
            init_chat_id, update_chat_id
        )
        return Response(response, status=status.HTTP_200_OK)
    except BadRequest as e:
        logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
        return Response(
            {"success": False, "message": "Invalid input. Please check the request."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        logger.error(f"{ERROR_PROCESSING_REQUEST_MESSAGE}: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def get_history(request, interactor: ConfigInteractor, chat_id_prefix):

    token = request.headers.get("Authorization")
    if not token:
        return Response(
            {"success": False, "message": "Authorization header is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    chat_id = chat_id_prefix + request.query_params.get("chat_id", "")
    if not chat_id:
        return Response(
            {"success": False, "message": "request parameter is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        messages = interactor.get_chat_history(token, chat_id)
        logger.info("Context cleared for chat_id: %s", chat_id)
        return Response(messages, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error("Error get_history: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def get_user_chat_history(request, interactor: ConfigInteractor, chat_id_prefix):

    token = request.headers.get("Authorization")
    if not token:
        return Response(
            {"success": False, "message": "Authorization header is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    chat_id = chat_id_prefix + request.query_params.get("chat_id", "")
    if not chat_id:
        return Response(
            {"success": False, "message": "request parameter is missing"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user_chat_history = interactor.get_user_chat_history(token, chat_id)
        logger.info("Context cleared for chat_id: %s", chat_id)
        return Response({"success": True, "message": user_chat_history.to_dict() if user_chat_history else []}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error get_user_chat_history: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def write_back_chat_cache(request, interactor, chat_id_prefix):
    try:
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"success": False, "message": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = chat_id_prefix + request.query_params.get("chat_id", "")
        if not chat_id:
            return Response(
                {"success": False, "message": "request parameter is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        interactor.save_chat(token, chat_id)
        return Response({"success": True, "message": f"Chat saved: {chat_id}"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error write_back_chat_cache: %s", e)
        logger.exception("An exception occurred")
        return Response(
            {"success": False, "message": f"Error processing chat workflow: {e}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

