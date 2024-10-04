import logging

from config_generator.config_interactor import ConfigInteractor
from .processor import TrinoProcessor
from common_utils.config import WORK_DIR, TRINO_PROMPT_PATH

logger = logging.getLogger("django")
INIT_REQUESTS_PREFIX = "init"

class TrinoInteractor(ConfigInteractor):

    def __init__(self, processor: TrinoProcessor):

        super().__init__(processor)
        self.processor = processor
        logger.info("Initializing TrinoInteractor...")

    def chat(self, token, chat_id, question, return_object, user_data):
        try:
            super().chat(token, chat_id, question, return_object, user_data)
            meta = self._get_cache_meta(token, chat_id)
            entity = self.cache_service.get(meta, chat_id)
            schema_name = entity.value
            result = self.processor.ask_question_agent(chat_id, schema_name, question)
            return {"success": True, "message": str(result)}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def run_query(self, query):
            result = self.processor.run_query(query)
            logger.info("Result set returned: %s", result)
            return {"success": True, "message": str(result)}


    def _initialize_trino(self, chat_id, schema_name):
        query = (
            'Execute query "SELECT * FROM information_schema.columns '
            f"WHERE table_schema = '{schema_name}' AND column_name NOT IN ('id', 'root_id', 'parent_id')\". "
            f"Tell me what you know about this schema after running the query, "
            f"what tables and columns do they have. Please use chat_id '{chat_id}'"
        )
        result = self.processor.ask_question_agent(chat_id, schema_name, query)
        prompt_path = f"{WORK_DIR}/{TRINO_PROMPT_PATH}"
        try:
            with open(prompt_path, "r") as file:
                prompt = file.read()
        except FileNotFoundError as e:
            raise e
        self.processor.ask_question_agent(chat_id,
                                          schema_name,
                                          f"Do your best to remember this instruction for further interactions. "
                                          f"{prompt}. You do not need to execute any queries here, just remember, how to do it")
        return result

