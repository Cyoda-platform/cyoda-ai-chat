import logging
from typing import List

from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH = "connections/"
QA_SYSTEM_PROMPT = """You are a data source connection generation tool. You should do your best to answer the question.
        You are aware of HttpEndpointDto.java object and data sources API. You should be able to map API docs to HttpEndpointDto.java object.
        Use the following pieces of retrieved context to answer the question.

        {context}"""
LLM_TEMPERATURE = 0.85
LLM_MAX_TOKENS = 4000
LLM_MODEL = "gpt-4o"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
processor = RagProcessor()
# not tread safe - will be replaced in the future
connections_chat_history = {}


class ConnectionProcessor:
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
        self.web_docs = self.get_web_script_docs()
        self.vectorstore = processor.init_vectorstore(
            CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH, self.web_docs
        )
        self.rag_chain = processor.process_rag_chain(
            self.vectorstore, self.llm, QA_SYSTEM_PROMPT
        )
        self.chat_history = ChatHistoryService(connections_chat_history)

    def get_web_script_docs(self):
        """
        Retrieves web documents for context.

        Returns:
            list: A list of web documents.
        """
        urls = [
            "https://velocity.apache.org/tools/devel/tools-summary.html",
            "https://velocity.apache.org/engine/2.3/vtl-reference.html",
        ]
        web_docs = processor.get_web_docs(urls)
        return web_docs

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

    def load_additional_sources(self, urls: List[str]):
        """
        Loads additional sources to the vector store

        Args:
            question (str): The question to ask.

        Returns:
            str: The answer with success message
        """

        return processor.load_additional_sources(self.vectorstore, urls)
