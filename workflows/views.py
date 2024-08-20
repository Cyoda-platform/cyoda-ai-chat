import logging
from rest_framework.response import Response
from rest_framework import status, views
from grpc_client.logic.grpc_client import GRPCClient
from .tools.entity_tools import EntityTools
logger = logging.getLogger('django')
grpc_client = GRPCClient()
entity_tools = EntityTools()

# Views
class InitialWorkflowView(views.APIView):
    """View to handle initial mapping requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to initialize a mapping."""
        logger.info("Starting InitialMappingView")


class ChatWorkflowView(views.APIView):
    """View to handle chat mapping requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat mapping."""
        logger.info("Starting ChatMappingView")


class ChatWorkflowClearView(views.APIView):
    """View to handle chat mapping clear requests."""

    def get(self, request):
        """Handle GET requests to clear a chat mapping."""
        logger.info("Starting ChatMappingClearView")


class ReturnDataView(views.APIView):
    """View to handle requests to return data."""

    def get(self, request):
        """Handle GET requests to return data."""
        logger.info("Starting ReturnDataView")
        

class GetWorkflowsList(views.APIView):
    """View to handle requests to return data."""

    def get(self, request):
        """Handle GET requests to return data."""
        logger.info("Starting ReturnDataView")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"error": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = request.query_params.get("chat_id")
        return Response(entity_tools.get_workflows_list(token, chat_id))
    
    
class GetWorkflowData(views.APIView):
    """View to handle requests to return data."""

    def get(self, request):
        """Handle GET requests to return data."""
        logger.info("Starting ReturnDataView")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"error": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        workflow_name = request.query_params.get("workflow_name")
        if not workflow_name:
            return Response(
                {"error": "workflow_name is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = request.query_params.get("chat_id")
        return Response(entity_tools.get_workflow_data(token, chat_id, workflow_name))
    
    
class SubmitWorkflowDataView(views.APIView):
    """View to handle chat mapping clear requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat mapping."""
        logger.info("Starting ChatMappingView")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"error": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = request.query_params.get("chat_id")
        return Response(entity_tools.validate_workflow_data(token, chat_id, request.data))
    
    
class SaveWorkflowDataView(views.APIView):
    """View to handle chat mapping clear requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat mapping."""
        logger.info("Starting ChatMappingView")
        token = request.headers.get("Authorization")
        if not token:
            return Response(
                {"error": "Authorization header is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat_id = request.query_params.get("chat_id")
        if not chat_id:
            return Response(
                {"error": "chat_id is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        workflow_name = request.query_params.get("workflow_name")
        if not workflow_name:
            return Response(
                {"error": "workflow_name is missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(entity_tools.save_workflow_entity(token, chat_id, workflow_name, request.data))
