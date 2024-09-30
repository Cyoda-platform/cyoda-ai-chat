import logging
from typing import List

from rag_processor.processor import RagProcessor
from common_utils.config import (
    LLM_TEMPERATURE_ADD_SCRIPT,
    LLM_MAX_TOKENS_ADD_SCRIPT,
    LLM_MODEL_ADD_SCRIPT,
    CYODA_AI_CONFIG_GEN_MAPPINGS_PATH
)

logger = logging.getLogger('django')

QA_SYSTEM_PROMPT = """You are a mapping generation code assistant assistant. \
You are an expert in Javascript Nashorn and understand how it is different from Java and javascript.
You will be asked to generate Nashorn javascript code to map input to entity.py. \
First, analyse the input and the entity.py and fill in Mapping Questionnaire.
Then do your best to do code assistance for mapping the input to the entity.py.   
{context}"""


class MappingProcessor(RagProcessor):
    def __init__(self):
        super().__init__(
            temperature=LLM_TEMPERATURE_ADD_SCRIPT,
            max_tokens=LLM_MAX_TOKENS_ADD_SCRIPT,
            model=LLM_MODEL_ADD_SCRIPT,
            openai_api_base=None,
            path=CYODA_AI_CONFIG_GEN_MAPPINGS_PATH,
            config_docs=self._get_web_script_docs(),
            system_prompt=QA_SYSTEM_PROMPT
        )

    def _get_web_script_docs(self) -> List[dict]:
        urls = [
            "https://docs.oracle.com/javase/8/docs/technotes/guides/scripting/prog_guide/javascript.html"
        ]
        logger.info("Fetching web documents from: %s", urls)
        return self.get_web_docs(urls)

    def ask_question(self, chat_id: str, question: str) -> str:
        logger.info("Asking question in chat %s: %s", chat_id, question)
        return self.ask_rag_question(chat_id, question)
