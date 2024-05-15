from django.urls import path
from . import views

urlpatterns = [
    path("<str:topic>/<str:user>/<int:index>", views.PromptView.as_view(), name="prompt_detail"),
    path("<str:topic>/<str:user>", views.PromptView.as_view(), name="prompts"),
]
