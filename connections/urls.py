from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialConnectionView.as_view(), name='connections-initial'),
    path('chat', views.ChatConnectionView.as_view(), name='connections-ai-chat'),
    path('chat-clear', views.ChatConnectionClearView.as_view(), name='connections-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='connections-return-data'),
    path('ingest-data', views.ChatIngestDataView.as_view(), name='connections-ingest-data'),
    path('initialized', views.ChatConnectionInitializedView.as_view(), name='connections-initialized'),
    path('chat-history', views.ChatConnectionGetChatHistoryView.as_view(), name='history'),
    path('update-id', views.ChatConnectionUpdateIdView.as_view(), name='update-id'),
    path('save-chat', views.ChatSaveChatView.as_view(), name='save-chat'),
    path('user-chat-history', views.ChatConnectionGetUserChatHistoryView.as_view(), name='user-chat-history'),
]