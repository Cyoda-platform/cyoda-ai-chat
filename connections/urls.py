from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialConnectionView.as_view(), name='connections-initial'),
    path('chat', views.ChatMappingView.as_view(), name='connections-ai-chat'),
    path('chat-clear', views.ChatMappingClearView.as_view(), name='connections-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='connections-return-data'),
]