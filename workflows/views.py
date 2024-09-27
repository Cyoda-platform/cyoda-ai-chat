import logging
from rest_framework.response import Response
from rest_framework import status, views
from .logic.interactor import WorkflowsInteractor
from .logic.prompts import RETURN_DATA
from .logic.processor import WorkflowProcessor
from .logic.workflow_gen_service import WorkflowGenerationService

logger = logging.getLogger('django')

interactor = WorkflowsInteractor(WorkflowProcessor(), WorkflowGenerationService())


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

