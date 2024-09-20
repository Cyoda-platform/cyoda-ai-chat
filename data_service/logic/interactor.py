import logging
from rest_framework.exceptions import APIException

from workflows.logic.interactor import initialized_requests
from .processor import TrinoProcessor
from common_utils.config import WORK_DIR, TRINO_PROMPT_PATH

logger = logging.getLogger("django")


class TrinoInteractor:
    initialized_requests = {}

    def __init__(self, processor: TrinoProcessor):

        logger.info("Initializing TrinoInteractor...")
        self.processor = processor

    def _log_and_raise_error(self, message, exception):

        logger.error(f"{message}: %s", exception, exc_info=True)
        raise APIException(detail=message) from exception

    def clear_context(self, chat_id):

        try:
            self.processor.chat_history.clear_chat_history(chat_id)
            if chat_id in self.initialized_requests:
                del self.initialized_requests[chat_id]
            return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            self._log_and_raise_error("An error occurred while clearing the context", e)

    def chat(self, chat_id, question):

        try:
            if chat_id not in self.initialized_requests:
                return {
                    "success": False,
                    "message": f"{chat_id} is not in initialized requests. Please initialize first.",
                }
            result = self.processor.ask_question_agent(chat_id, self.initialized_requests[chat_id], question)
            return {"success": True, "message": str(result)}
        except Exception as e:
            self._log_and_raise_error("An error occurred while processing the chat", e)

    def run_query(self, query):

        try:
            result = self.processor.run_query(query)
            logger.info("Resultset returned: %s", result)
            return {"success": True, "message": str(result)}
        except Exception as e:
            self._log_and_raise_error("An error occurred while running the query", e)

    def initialize(self, chat_id, schema_name):

        try:
            self.clear_context(chat_id)
            # result = self._initialize_trino(chat_id, schema_name)
            self.initialized_requests[chat_id] = schema_name
            return {"success": True, "message": chat_id}
        except Exception as e:
            self._log_and_raise_error("An error occurred while initializing the chat", e)

    def _initialize_trino(self, chat_id, schema_name):
        query = (
            'Execute query "SELECT * FROM information_schema.columns '
            f"WHERE table_schema = '{schema_name}' AND column_name NOT IN ('id', 'root_id', 'parent_id')\". "
            f"Tell me what you know about this schema after running the query, "
            f"what tables and columns do they have. Please use chat_id '{chat_id}'"
        )
        result = self.processor.ask_question_agent(chat_id, query)
        prompt_path = f"{WORK_DIR}/{TRINO_PROMPT_PATH}"
        try:
            with open(prompt_path, "r") as file:
                prompt = file.read()
        except FileNotFoundError as e:
            self._log_and_raise_error(f"Prompt file not found at {prompt_path}", e)
        self.processor.ask_question_agent(chat_id,
                                          f"Do your best to remember this instruction for further interactions. "
                                          f"{prompt}. You do not need to execute any queries here, just remember, how to do it")
        return result
