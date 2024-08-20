import logging
from typing import List
from common_utils.utils import (
    get_env_var,
)
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH = "workflows/"
QA_SYSTEM_PROMPT = """You are a workflow assistant. Use your common knowledge to answer the questions.
{context}"""
LLM_TEMPERATURE = float(get_env_var("LLM_TEMPERATURE_WORKFLOW"))
LLM_MAX_TOKENS = int(get_env_var("LLM_MAX_TOKENS_ADD_WORKFLOW"))
LLM_MODEL = get_env_var("LLM_MODEL_ADD_WORKFLOW")

logger = logging.getLogger('django')

processor = RagProcessor()
# not tread safe - will be replaced in the future
connections_chat_history = {}


class WorkflowProcessor:
    """
    A class to process connections and ask questions related to data source generation.

    Attributes:
        llm (LanguageModel): The language model used for processing.
        web_docs (list): A list of web documents used for context in the RAG chain.
        rag_chain (RagChain): The RAG chain used for processing questions.
        chat_history (ChatHistoryService): The service for managing chat history.

    Methods:
        __init__(): Initializes the ConnectionProcessor instance.
        get_web_script_docs(): Retrieves web documents for context.
        ask_question(chat_id, question): Asks a question using the RAG chain and returns the answer.
    """

    def __init__(self):
        """
        Initializes the ConnectionProcessor instance.
        """
        self.llm = processor.initialize_llm(
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model=LLM_MODEL,
            openai_api_base=None,
        )

        logger.info("LOADING DOCS FOR IMPORT CONFIG")
        self.vectorstore = processor.init_vectorstore(
            CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH, None
        )
        self.rag_chain = processor.process_rag_chain(
            self.vectorstore, self.llm, QA_SYSTEM_PROMPT
        )
        self.chat_history = ChatHistoryService(connections_chat_history)

    def ask_question(self, chat_id, question):
        """
        Asks a question using the RAG chain and returns the answer.

        Args:
            chat_id (str): The ID of the chat session.
            question (str): The question to ask.

        Returns:
            str: The answer to the question.
        """
        answer = processor.ask_question(
            chat_id, question, self.chat_history, self.rag_chain
        )
        return answer
