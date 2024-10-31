import logging

from rest_framework import status, views

from config_generator import config_view_functions
from cyoda.logic.interactor import CyodaInteractor, chat_id_prefix
from cyoda.logic.processor import CyodaProcessor

logger = logging.getLogger('django')
interactor = CyodaInteractor(CyodaProcessor())


class InitialView(views.APIView):

    def post(self, request, *args, **kwargs):
        return config_view_functions.initial(request, interactor, chat_id_prefix)


class ChatInitializedView(views.APIView):

    def get(self, request):
        return config_view_functions.is_initialized(request, interactor, chat_id_prefix)


class ChatView(views.APIView):

    def post(self, request, *args, **kwargs):
        return config_view_functions.chat(request, interactor, chat_id_prefix)


class ChatClearView(views.APIView):

    def get(self, request):
        return config_view_functions.chat_clear(request, interactor, chat_id_prefix)


class ReturnDataView(views.APIView):

    def get(self, request):
        return config_view_functions.return_data([])


class ChatUpdateIdView(views.APIView):
    def put(self, request, *args, **kwargs):
        return config_view_functions.update_id(request, interactor, chat_id_prefix)


class ChatGetChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_history(request, interactor, chat_id_prefix)


class ChatSaveChatView(views.APIView):

    def get(self, request):
        return config_view_functions.write_back_chat_cache(request, interactor, chat_id_prefix)


class ChatGetUserChatHistoryView(views.APIView):

    def get(self, request):
        return config_view_functions.get_user_chat_history(request, interactor, chat_id_prefix)
