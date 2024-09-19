import logging
from typing import List, Dict
from common_utils.config import (
    LLM_TEMPERATURE_ADD_CONNECTION,
    LLM_MAX_TOKENS_ADD_CONNECTION,
    LLM_MODEL_ADD_CONNECTION,
    CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH
)
from rag_processor.processor import RagProcessor

QA_SYSTEM_PROMPT = """You are a connection generation assistant. \
You will be asked to generate connection configurations. \
First, analyse the human message and choose a template to fill in: [Connections Questionnaire, HttpConnectionDetailsDto, HttpEndpointDto] \
Then fill in the values inside $ with curly brackets in the template. Other values in the template should be preserved. Treat it like a test where you need to fill in the blanks. But you cannot modify values out of the scope of your test. \
Construct and return only the json for the bean you are asked for. Return the resulting json without any comments.  
{context}"""

logger = logging.getLogger('django')


class ConnectionProcessor(RagProcessor):

    def __init__(self):
        super().__init__(
            temperature=LLM_TEMPERATURE_ADD_CONNECTION,
            max_tokens=LLM_MAX_TOKENS_ADD_CONNECTION,
            model=LLM_MODEL_ADD_CONNECTION,
            openai_api_base=None,
            path=CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH,
            config_docs=self.get_web_script_docs(),
            system_prompt=QA_SYSTEM_PROMPT
        )

    def get_web_script_docs(self) -> List[Dict]:
        """Fetches web documents for the specified URLs."""
        urls = [
            "https://velocity.apache.org/tools/devel/tools-summary.html",
            "https://velocity.apache.org/engine/2.3/vtl-reference.html",
        ]
        logger.info("Loading web documents from: %s", urls)
        return self.get_web_docs(urls)

    def ask_question(self, chat_id: str, question: str) -> str:
        """Asks a question using the RAG chain and updates chat history."""
        return self.ask_rag_question(chat_id, question)

    def load_additional_sources(self, urls: List[str]) -> Dict[str, str]:
        """Loads additional sources into the vector store."""
        return self.load_additional_rag_sources(urls)
