import logging
from rest_framework.exceptions import APIException
from .processor import TrinoProcessor

logger = logging.getLogger("django")
initialized_requests = set()
processor = TrinoProcessor()

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
            result = processor.ask_question(chat_id, question)
            return {"success": True, "message": f"{result}"}
        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)
            
    def initialize(self, chat_id):
        try:
            result = processor.ask_question(chat_id, f"What tables do you have? PLease use chat_id '{chat_id}'")
            return {"success": True, "message": f"{result}"}
        except Exception as e:
            self.log_and_raise_error("An error occurred while processing the chat", e)