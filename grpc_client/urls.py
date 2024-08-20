from django.urls import path
from . import views

urlpatterns = [
    path('grpc-async-view', views.GRPCAsyncView.as_view(), name='grpc_async_view'),
]