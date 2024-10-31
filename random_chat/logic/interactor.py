import logging

from config_generator.config_interactor import ConfigInteractor
from .processor import RandomProcessor

logger = logging.getLogger('django')
chat_id_prefix = "random"

class RandomInteractor(ConfigInteractor):
    """
    A class that interacts with mappings for a chat system.
    """

    def __init__(self, processor: RandomProcessor):

        super().__init__(processor)
        logger.info("Initializing Random Interactor...")
        self.processor = processor

    def chat(self, token, chat_id, question, return_object, user_data):
        super().chat(token, chat_id, question, "chat", None)
        result = self.processor.ask_question(chat_id, question)
        return {"success": True, "message": result}