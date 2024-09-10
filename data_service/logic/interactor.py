import logging
from rest_framework.exceptions import APIException
from .processor import TrinoProcessor
from common_utils.utils import (
    get_env_var,
)
ENV = get_env_var("ENV")
WORK_DIR = (
    get_env_var("WORK_DIR") if ENV.lower() == "local" else get_env_var("GIT_WORK_DIR")
)
logger = logging.getLogger("django")
initialized_requests = set()
processor = TrinoProcessor()
LLM_MODEL = get_env_var("LLM_MODEL_TRINO")


class TrinoInteractor:
    def __init__(self):
        logger.info("Initializing TrinoInteractor...")

    def log_and_raise_error(self, message, exception):
        logger.error(f"{message}: %s", exception, exc_info=True)
        raise APIException(message, exception)

    def clear_context(self, chat_id):
        # Validate input
        try:
            # Clear chat history
            processor.chat_history.clear_chat_history(chat_id)
            if chat_id in initialized_requests:
                initialized_requests.remove(chat_id)
                return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            logger.error(
                "An error occurred while clearing the context: %s", e, exc_info=True
            )
            raise APIException("An error occurred while clearing the context.", e)

    def chat(self, chat_id, question):
        try:
            if chat_id not in initialized_requests:
                return {"success": False, "message": f"{chat_id} is not in initialized requests. PLease initialize first."}
            result = processor.ask_question_agent(chat_id, question)
            return {"success": True, "message": f"{result}"}
        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)

    def run_query(self, query):
        try:
            result = processor.run_query(query)
            logger.info("resultset returned=%s", result)
            return {"success": True, "message": f"{result}"}
        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)

    def initialize(self, chat_id, schema_name):
        try:
            self.clear_context(chat_id)
            result = processor.ask_question_agent(
                chat_id,
                f"Execute query \"SELECT * FROM information_schema.columns WHERE table_schema = '{schema_name}' AND column_name != 'id' AND column_name != 'root_id' AND column_name != 'parent_id'\". Tell me what you know about this schema after running the query, what tables and columns do they have. Please use chat_id '{chat_id}'",
            )
            prompt = ""
            with open(f"{WORK_DIR}/data/rag/v1/trino/trino.txt", "r") as file:
                prompt = file.read()
            processor.ask_question(
                chat_id,
                prompt,
            )
            initialized_requests.add(chat_id)
            return {"success": True, "message": f"{result}"}
        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)
