import base64
import logging
from typing import List

from langchain_core.messages import HumanMessage

from rag_processor.processor import RagProcessor
from common_utils.config import (CYODA_AI_CONFIG_GEN_CYODA_PATH, LLM_MODEL_CYODA, LLM_MAX_TOKENS_CYODA,
                                 LLM_TEMPERATURE_CYODA, LLM_MODEL_CYODA_API_BASE)

logger = logging.getLogger('django')

QA_SYSTEM_PROMPT = """You are a cyoda application builder assistant.   
{context}"""


class CyodaProcessor(RagProcessor):
    def __init__(self):
        super().__init__(
            temperature=LLM_TEMPERATURE_CYODA,
            max_tokens=LLM_MAX_TOKENS_CYODA,
            model=LLM_MODEL_CYODA,
            openai_api_base=LLM_MODEL_CYODA_API_BASE,
            path=CYODA_AI_CONFIG_GEN_CYODA_PATH,
            config_docs=[],
            system_prompt=QA_SYSTEM_PROMPT
        )

    def _get_web_script_docs(self) -> List[dict]:
        urls = [
            "https://medium.com/@paul_42036/entity-workflows-for-event-driven-architectures-4d491cf898a5",
            "https://medium.com/@paul_42036/whats-an-entity-database-11f8538b631a"
        ]
        logger.info("Fetching web documents from: %s", urls)
        return self.get_web_docs(urls)

    def ask_question(self, chat_id: str, question: str) -> str:
        logger.info("Asking question in chat %s: %s", chat_id, question)
        return self.ask_rag_question(chat_id, question)

    def image_description(self, image_file, mime_type) -> str:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        file_format = mime_type.split("/")[-1]
        question = "Please give me maximum information from this image, that I can use for Cyoda App design. Return no less than 70 words. If it is a diagram, you can return Markup text, which correctly describes relations and connections in this data. Provide as much relevant information as possible."
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"{question}"},
                {"type": "image_url", "image_url": {"url": f"data:image/{file_format};base64,{image_data}"}},
            ]
        )
        response = self.llm.invoke([message])
        return response.content