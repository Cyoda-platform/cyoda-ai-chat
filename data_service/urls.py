from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialTrinoView.as_view(), name='trino-initial'),
    path('chat', views.ChatTrinoView.as_view(), name='trino-ai-chat'),
    path('run-query', views.ChatTrinoRunQueryView.as_view(), name='trino-ai-run-query'),
    path('chat-clear', views.ChatTrinoClearView.as_view(), name='trino-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='trino-return-data'),
    path('initialized', views.ChatTrinoInitializedView.as_view(), name='trino-initialized'),
    path('chat-history', views.ChatTrinoGetChatHistoryView.as_view(), name='history'),
    path('update-id', views.ChatTrinoUpdateIdView.as_view(), name='update-id'),
    path('save-chat', views.ChatSaveChatView.as_view(), name='save-chat'),
    path('user-chat-history', views.ChatTrinoGetUserChatHistoryView.as_view(), name='user-chat-history'),
]