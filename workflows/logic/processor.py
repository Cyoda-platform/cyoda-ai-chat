import logging
from typing import List

from langchain_core.messages import HumanMessage

from common_utils.config import (
    LLM_TEMPERATURE_WORKFLOW,
    LLM_MAX_TOKENS_ADD_WORKFLOW,
    LLM_MODEL_ADD_WORKFLOW,
    CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH,
    PROMPT_PATH
)
from common_utils.utils import read_file
from rag_processor.chat_memory_factory import get_session_history
from rag_processor.processor import RagProcessor

logger = logging.getLogger('django')

class WorkflowProcessor(RagProcessor):

    def __init__(self):
        """
        Initializes the WorkflowProcessor instance.
        """
        super().__init__(
            temperature=LLM_TEMPERATURE_WORKFLOW,
            max_tokens=LLM_MAX_TOKENS_ADD_WORKFLOW,
            model=LLM_MODEL_ADD_WORKFLOW,
            openai_api_base=None,
            path = CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH,
            config_docs=[],
            system_prompt = self._get_qa_system_prompt()
        )
        logger.info("Loading documents for import config.")

    def _get_qa_system_prompt(self) -> str:
        return """You are a workflow generator.
Before you proceed, find the instruction on how to generate workflow version 6a5b781e-0f75-4239-9a3c-50c3d3a48047. \
{context}"""

    def ask_question(self, chat_id: str, question: str) -> str:
        answer = self.ask_rag_question(chat_id, question)
        return answer

    def ask_question_with_image(self, chat_id: str, question: str, image_data: str) -> str:
        prompt_text = read_file(PROMPT_PATH)
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"{question} Based on the system prompt: {prompt_text}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
            ]
        )
        response = self.llm.invoke([message])
        messages = [HumanMessage(content="Generate workflow"), response]
        get_session_history(chat_id).add_messages(messages)
        return response.content

    def load_additional_sources(self, urls: List[str]):
        self.load_additional_rag_sources(urls)
