import logging
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

CYODA_AI_CONFIG_GEN_MAPPINGS_PATH = "mappings/"
QA_SYSTEM_PROMPT = """You are a mapping tool. You should do your best to answer the question.
        Use the following pieces of retrieved context to answer the question. \
        {context}"""


logging.basicConfig(level=logging.INFO)
processor = RagProcessor()
mapping_chat_history = {}


class MappingProcessor:
    """
    A class for processing mapping questions.

    Attributes:
        llm (LanguageModel): The language model for generating responses.
        rag_chain (RagChain): The RAG chain for processing questions.
        chat_history (ChatHistoryService): The service for managing chat history.

    Methods:
        get_web_script_docs: Retrieves web documents for scripting.
        ask_question: Processes a question and returns an answer.
    """

    def __init__(self):
        """
        Initializes the MappingProcessor instance.

        Sets up the language model, RAG chain, and chat history service.
        """
        self.llm = processor.initialize_llm()
        web_docs = self.get_web_script_docs()
        self.rag_chain = processor.process_rag_chain(
            self.llm, QA_SYSTEM_PROMPT, CYODA_AI_CONFIG_GEN_MAPPINGS_PATH, web_docs
        )
        self.chat_history = ChatHistoryService(mapping_chat_history)

    def get_web_script_docs(self):
        """
        Retrieves web documents for scripting.

        Returns:
            list: A list of web documents for scripting.
        """
        urls = [
            "https://docs.oracle.com/javase/8/docs/technotes/guides/scripting/prog_guide/javascript.html"
        ]
        web_docs = processor.get_web_docs(urls)
        return web_docs

    def ask_question(self, chat_id, question):
        """
        Processes a question and returns an answer.

        Args:
            chat_id (str): The ID of the chat session.
            question (str): The question to be answered.

        Returns:
            str: The answer to the question.
        """
        answer = processor.ask_question(chat_id, question, self.chat_history, self.rag_chain)
        return answer