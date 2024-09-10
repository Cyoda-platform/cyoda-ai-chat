import logging
from rest_framework.response import Response
from rest_framework import status, views

from grpc_client.logic.grpc_client import GRPCClient
from .tools.entity_tools import EntityTools
from .logic.interactor import WorkflowsInteractor
from .logic.prompts import RETURN_DATA

# Configure logging
logger = logging.getLogger('django')

# Initialize external dependencies
grpc_client = GRPCClient()
entity_tools = EntityTools()
interactor = WorkflowsInteractor()


class BaseWorkflowView(views.APIView):
    """Base view for workflow-related endpoints."""

    def handle_missing_authorization(self):
        """Handle missing Authorization header."""
        return Response(
            {"error": "Authorization header is missing"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def handle_missing_query_param(self, param_name):
        """Handle missing query parameter."""
        return Response(
            {f"{param_name} is missing"},
            status=status.HTTP_400_BAD_REQUEST
        )


class InitialWorkflowView(BaseWorkflowView):
    """View to handle initial workflow requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to initialize a workflow."""
        logger.info("Starting InitialworkflowView")
        # Add logic for initial workflow here
        return Response({"message": "Initial workflow started"}, status=status.HTTP_200_OK)


class ChatWorkflowView(BaseWorkflowView):
    """View to handle chat workflow requests."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to process a chat workflow."""
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        try:
            logger.info("Starting ChatworkflowView")
            response_data = interactor.chat(request, token)
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error processing chat workflow: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatWorkflowClearView(BaseWorkflowView):
    """View to handle chat workflow clear requests."""

    def get(self, request):
        """Handle GET requests to clear a chat workflow."""
        logger.info("Starting ChatworkflowClearView")
        chat_id = request.query_params.get("chat_id")
        if not chat_id:
            return self.handle_missing_query_param("chat_id")

        response_data = interactor.clear_context(chat_id)
        return Response(response_data, status=status.HTTP_200_OK)


class ReturnDataView(BaseWorkflowView):
    """
    View to handle requests to return data.
    """

    def get(self, request):
        """
        Handle GET requests to return data.
        """
        return_data = RETURN_DATA
        logger.info("Returning data")
        return Response(return_data)

class GetWorkflowsList(BaseWorkflowView):
    """View to handle requests to return workflows list."""

    def get(self, request):
        """Handle GET requests to return workflows list."""
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        chat_id = request.query_params.get("chat_id")
        response_data = entity_tools.get_workflows_list(token, chat_id)
        return Response(response_data)
    
    
class GetWorkflowData(BaseWorkflowView):
    """View to handle requests to return workflow data."""

    def get(self, request):
        """Handle GET requests to return workflow data."""
        logger.info("Starting GetWorkflowData")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        workflow_name = request.query_params.get("workflow_name")
        if not workflow_name:
            return self.handle_missing_query_param("workflow_name")

        chat_id = request.query_params.get("chat_id")
        response_data = entity_tools.get_workflow_data(token, chat_id, workflow_name)
        return Response(response_data)

class SubmitWorkflowDataView(BaseWorkflowView):
    """View to handle requests to submit workflow data."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to submit workflow data."""
        logger.info("Starting SubmitWorkflowDataView")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        chat_id = request.query_params.get("chat_id")
        response_data = entity_tools.validate_workflow_data(token, chat_id, request.data)
        return Response(response_data)

class SaveWorkflowDataView(BaseWorkflowView):
    """View to handle requests to save workflow data."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to save workflow data."""
        logger.info("Starting SaveWorkflowDataView")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        chat_id = request.query_params.get("chat_id")
        if not chat_id:
            return self.handle_missing_query_param("chat_id")

        workflow_name = request.query_params.get("workflow_name")
        if not workflow_name:
            return self.handle_missing_query_param("workflow_name")

        response_data = entity_tools.save_workflow_entity(token, chat_id, workflow_name, request.data)
        return Response(response_data)

class GetTransitionsList(BaseWorkflowView):
    """View to handle requests to get transitions list."""

    def get(self, request):
        """Handle GET requests to return transitions list."""
        logger.info("Starting GetTransitionsList")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        entity_id = request.query_params.get("entity_id")
        if not entity_id:
            return self.handle_missing_query_param("entity_id")

        entity_class = request.query_params.get("entity_class")
        if not entity_class:
            return self.handle_missing_query_param("entity_class")

        workflow_id = request.query_params.get("workflow_id")
        if not workflow_id:
            return self.handle_missing_query_param("workflow_id")

        response_data = interactor.get_next_transitions(token, workflow_id, entity_id, entity_class)
        return Response(response_data)

class LaunchTransition(BaseWorkflowView):
    """View to handle requests to launch a transition."""

    def put(self, request):
        """Handle PUT requests to launch a transition."""
        logger.info("Starting LaunchTransition")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()

        entity_id = request.query_params.get("entity_id")
        if not entity_id:
            return self.handle_missing_query_param("entity_id")

        entity_class = request.query_params.get("entity_class")
        if not entity_class:
            return self.handle_missing_query_param("entity_class")

        transition_name = request.query_params.get("transition_name")
        if not transition_name:
            return self.handle_missing_query_param("transition_name")

        response_data = interactor.launch_transition(token, transition_name, entity_id, entity_class)
        return Response(response_data)

class GenerateWorkflowConfigView(BaseWorkflowView):
    """View to handle requests to generate workflow configuration."""

    def post(self, request, *args, **kwargs):
        """Handle POST requests to generate workflow configuration."""
        logger.info("Starting GenerateWorkflowConfigView")
        token = request.headers.get("Authorization")
        if not token:
            return self.handle_missing_authorization()
        class_name = request.data.get("class_name")
        if not class_name:
            return self.handle_missing_query_param("class_name")
        response_data = interactor.save_workflow_entity(token, request.data, class_name)
        return Response(response_data)

