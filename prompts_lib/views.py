from rest_framework import status, views
from rest_framework.response import Response
from .prompts_library_service import PromptService

promptService = PromptService()

class PromptView(views.APIView):
    def get(self, request, topic, user, index=None):
        if index is not None:
            prompt = promptService.get_prompt(topic, user, index)
            if prompt is None:
                return Response(
                    {"error": "Prompt not found"}, status=status.HTTP_404_NOT_FOUND
                )
            return Response(prompt, status=status.HTTP_200_OK)
        prompts = promptService.get_prompts(topic, user)
        return Response(prompts, status=status.HTTP_200_OK)

    def post(self, request, topic, user):
        prompt = request.data.get("prompt")
        if not prompt:
            return Response(
                {"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        promptService.add_prompt(topic, user, prompt)
        return Response({"message": "Prompt added"}, status=status.HTTP_201_CREATED)

    def delete(self, request, topic, user, index):
        promptService.delete_prompt(topic, user, index)
        return Response(
            {"message": "Prompt deleted"}, status=status.HTTP_204_NO_CONTENT
        )
