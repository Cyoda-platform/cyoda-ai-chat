from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialConnectionView.as_view(), name='connections-initial'),
    path('chat', views.ChatConnectionView.as_view(), name='connections-ai-chat'),
    path('chat-clear', views.ChatConnectionClearView.as_view(), name='connections-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='connections-return-data'),
    path('ingest-data', views.ChatIngestDataView.as_view(), name='connections-ingest-data'),
    path('import-connection', views.ChatImportConnectionView.as_view(), name='connections-import-config'),
]