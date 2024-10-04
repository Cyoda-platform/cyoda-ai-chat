from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialMappingView.as_view(), name='mappings-initial'),
    path('chat', views.ChatMappingView.as_view(), name='mappings-ai-chat'),
    path('chat-clear', views.ChatMappingClearView.as_view(), name='mappings-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='return-data'),
    path('initialized', views.ChatMappingInitializedView.as_view(), name='mappings-initialized'),
    path('chat-history', views.ChatMappingGetChatHistoryView.as_view(), name='history'),
    path('update-id', views.ChatMappingUpdateIdView.as_view(), name='update-id'),
]