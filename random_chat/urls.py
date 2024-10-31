from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialView.as_view(), name='cyoda-initial'),
    path('chat', views.ChatView.as_view(), name='cyoda-ai-chat'),
    path('chat-clear', views.ChatClearView.as_view(), name='cyoda-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='return-data'),
    path('initialized', views.ChatInitializedView.as_view(), name='cyoda-initialized'),
    path('chat-history', views.ChatGetChatHistoryView.as_view(), name='history'),
    path('update-id', views.ChatUpdateIdView.as_view(), name='update-id'),
    path('save-chat', views.ChatSaveChatView.as_view(), name='save-chat'),
    path('user-chat-history', views.ChatGetUserChatHistoryView.as_view(), name='user-chat-history'),
]