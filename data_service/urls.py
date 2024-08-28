from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialTrinoView.as_view(), name='trino-initial'),
    path('chat', views.ChatTrinoView.as_view(), name='trino-ai-chat'),
    path('run-query', views.ChatTrinoRunQueryView.as_view(), name='trino-ai-run-query'),
    path('chat-clear', views.ChatTrinoClearView.as_view(), name='trino-chat-clear')
]