import logging
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService
from common_utils.utils import (
    get_env_var,
)
CYODA_AI_CONFIG_GEN_MAPPINGS_PATH = "mappings/"
QA_SYSTEM_PROMPT = """You are a mapping generation code assistant assistant. \
You are an expert in Javascript Nashorn and understand how it is different from Java and javascript.
You will be asked to generate Nashorn javascript code to map input to entity. \
First, analyse the input and the entity and fill in Mapping Questionnaire.
Then do your best to do code assistance for mapping the input to the entity.   
{context}"""

LLM_TEMPERATURE = float(get_env_var("LLM_TEMPERATURE_ADD_SCRIPT"))
LLM_MAX_TOKENS = int(get_env_var("LLM_MAX_TOKENS_ADD_SCRIPT"))
LLM_MODEL = get_env_var("LLM_MODEL_ADD_SCRIPT")

logger = logging.getLogger('django')
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
        self.llm = processor.initialize_llm(
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model=LLM_MODEL,
            openai_api_base=None,
        )
        web_docs = self.get_web_script_docs()
        self.vectorstore = processor.init_vectorstore(
            CYODA_AI_CONFIG_GEN_MAPPINGS_PATH, web_docs
        )
        self.rag_chain = processor.process_rag_chain(
            self.vectorstore, self.llm, QA_SYSTEM_PROMPT
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
        answer = processor.ask_question(
            chat_id, question, self.chat_history, self.rag_chain
        )
        return answer
