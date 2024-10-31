import logging
from typing import List

from rag_processor.processor import RagProcessor
from common_utils.config import (CYODA_AI_CONFIG_GEN_CYODA_PATH, LLM_MODEL_CYODA, LLM_MAX_TOKENS_CYODA,
                                 LLM_TEMPERATURE_CYODA)

logger = logging.getLogger('django')

QA_SYSTEM_PROMPT = """You are a cyoda application builder assistant.   
{context}"""


class CyodaProcessor(RagProcessor):
    def __init__(self):
        super().__init__(
            temperature=LLM_TEMPERATURE_CYODA,
            max_tokens=LLM_MAX_TOKENS_CYODA,
            model=LLM_MODEL_CYODA,
            openai_api_base=None,
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
