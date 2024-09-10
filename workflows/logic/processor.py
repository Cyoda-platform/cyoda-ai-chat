import logging
from langchain_core.messages import HumanMessage
from common_utils.utils import get_env_var, read_file
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

# Configuration constants
CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH = "workflows/"
ENV = get_env_var("ENV").lower()
WORK_DIR = get_env_var("WORK_DIR") if ENV == "local" else get_env_var("GIT_WORK_DIR")
PROMPT_PATH = f"{WORK_DIR}/data/v1/workflows/prompt.txt"

# Load configuration values
LLM_TEMPERATURE = float(get_env_var("LLM_TEMPERATURE_WORKFLOW"))
LLM_MAX_TOKENS = int(get_env_var("LLM_MAX_TOKENS_ADD_WORKFLOW"))
LLM_MODEL = get_env_var("LLM_MODEL_ADD_WORKFLOW")

# Initialize logger
logger = logging.getLogger('django')

# Initialize processor and chat history
processor = RagProcessor()
workflow_chat_history = {}

class WorkflowProcessor:
    """
    A class to handle workflow generation and question processing.

    Attributes:
        llm (LanguageModel): The language model used for processing.
        vectorstore (VectorStore): The vector store used for context retrieval.
        rag_chain (RagChain): The RAG chain for question processing.
        chat_history (ChatHistoryService): Service for managing chat history.
    """

    def __init__(self):
        """
        Initializes the WorkflowProcessor instance.
        """
        self.llm = processor.initialize_llm(
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model=LLM_MODEL,
            openai_api_base=None,
        )

        logger.info("Loading documents for import config.")
        self.vectorstore = processor.init_vectorstore(
            CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH, None
        )
        self.rag_chain = processor.process_rag_chain(
            self.vectorstore, self.llm, self._get_qa_system_prompt()
        )
        self.chat_history = ChatHistoryService(workflow_chat_history)

    def _get_qa_system_prompt(self):
        """
        Retrieves the QA system prompt from the prompt file.

        Returns:
            str: The QA system prompt.
        """
        #prompt = read_file(PROMPT_PATH)
        return """You are a workflow generator.
Before you proceed, find the instruction on how to generate workflow version 6a5b781e-0f75-4239-9a3c-50c3d3a48047. \
{context}"""

    def ask_question(self, chat_id, question):
        """
        Asks a question and returns the answer.

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

    def ask_question_with_image(self, chat_id, question, image_data):
        """
        Asks a question with an image and returns the answer.

        Args:
            chat_id (str): The ID of the chat session.
            question (str): The question to ask.
            image_data (str): The base64-encoded image data.

        Returns:
            str: The answer to the question.
        """
        prompt_text = read_file(PROMPT_PATH)
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"{question} Based on the system prompt: {prompt_text}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
            ]
        )
        response = self.llm.invoke([message])
        self.chat_history.add_to_chat_history(chat_id, "Generate workflow", response)
        return response.content

    def load_additional_sources(self, urls):
        """
        Loads additional sources into the vector store.

        Args:
            urls (list): List of URLs to load.

        Returns:
            None
        """
        processor.load_additional_sources(self.vectorstore, urls)