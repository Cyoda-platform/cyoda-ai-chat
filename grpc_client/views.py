from django.http import JsonResponse
from django.views import View

from .logic.grpc_client import GRPCClient

class GRPCAsyncView(View):

    async def get(self, request, *args, **kwargs):
        grpc_client = await GRPCClient.create()
        # Now you can use grpc_client for your gRPC calls
        return JsonResponse({'status': 'gRPC client initialized'})
