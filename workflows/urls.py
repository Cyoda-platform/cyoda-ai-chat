from django.urls import path
from . import views

urlpatterns = [
    path('initial', views.InitialWorkflowView.as_view(), name='workflow-initial'),
    path('chat', views.ChatWorkflowView.as_view(), name='workflow-ai-chat'),
    path('chat-clear', views.ChatWorkflowClearView.as_view(), name='workflow-chat-clear'),
    path('return-data', views.ReturnDataView.as_view(), name='return-data'),
    path('get-workflows', views.GetWorkflowsList.as_view(), name='list-workflows'),
    path('get-workflow-data', views.GetWorkflowData.as_view(), name='get-workflow-data'),
    path('validate-workflow-data', views.SubmitWorkflowDataView.as_view(), name='validate-workflow-data'),
    path('save-workflow', views.SaveWorkflowDataView.as_view(), name='save-workflow'),
    path('next-transitions', views.GetTransitionsList.as_view(), name='next-transitions'),
    path('launch-transition', views.LaunchTransition.as_view(), name='launch-transition'),

]