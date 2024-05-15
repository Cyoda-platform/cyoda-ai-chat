import logging
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH = "connections/"
QA_SYSTEM_PROMPT = """You are a data source connection generation tool. You should do your best to answer the question.
        You are aware of HttpEndpointDto.java object and data sources API. You should be able to map API docs to HttpEndpointDto.java object.
        Use the following pieces of retrieved context to answer the question.

        {context}"""

logging.basicConfig(level=logging.INFO)
processor = RagProcessor()
#not tread safe - will be replaced in the future
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
        #gpt-3.5-turbo-16k	
        #gpt-4
        self.llm = processor.initialize_llm(temperature=0.85, max_tokens=4000, model = "gpt-4o", openai_api_base=None)
        self.web_docs = self.get_web_script_docs()
        self.rag_chain = processor.process_rag_chain(
            self.llm, QA_SYSTEM_PROMPT, CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH, self.web_docs
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
        answer = processor.ask_question(chat_id, question, self.chat_history, self.rag_chain)
        return answer