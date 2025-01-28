import logging

from common_utils.utils import process_uploaded_file, append_file_content_to_question
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

    def chat(self, token, chat_id, question, return_object, user_data, user_file=None):
        super().chat(token, chat_id, question, "chat", None)

        if user_file:
            file_content, metadata = process_uploaded_file(self, user_file)
            if file_content is None:
                return {"success": False, "message": metadata.get("error", f"Error processing file: {user_file.name}")}
            question = append_file_content_to_question(question, file_content, metadata)

        result = self.processor.ask_question(chat_id, question)
        return {"success": True, "message": result}