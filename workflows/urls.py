from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialWorkflowView.as_view(), name='workflow-initial'),
    path('chat', views.ChatWorkflowView.as_view(), name='workflow-ai-chat'),
    path('chat-clear', views.ChatWorkflowClearView.as_view(), name='workflow-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='return-data'),
    path('generate-workflow', views.GenerateWorkflowConfigView.as_view(), name='generate-workflow'),

]