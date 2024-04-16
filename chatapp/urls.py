from django.urls import path
from . import views

urlpatterns = [
    path('mappings-initial', views.InitialMappingView.as_view(), name='mappings-initial'),
    path('mappings-script', views.ScriptMappingView.as_view(), name='mappings-script'),
    path('mappings-ai-chat', views.ChatMappingView.as_view(), name='mappings-ai-chat'),
    path('mappings-chat-clear', views.ChatMappingClearView.as_view(), name='mappings-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='return-data'),

]