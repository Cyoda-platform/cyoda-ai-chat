import logging
from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import BaseMessage

from middleware.repository.entity.cache_entity import CacheEntity
from rag_processor.caching_service_factory import get_caching_service
from rag_processor.chat_memory_factory import get_session_history
from rag_processor.processor import RagProcessor
from rest_framework.exceptions import APIException


logger = logging.getLogger("django")
INIT_REQUESTS_PREFIX = "init"
INIT_META_CACHE_TTL = 31536000


class ConfigInteractor(ABC):

    def __init__(self, processor: RagProcessor):
        self.processor = processor
        self.cache_service = get_caching_service()

    def initialize_chat(self, token, chat_id, value):
        try:
            meta, key = self._get_meta_key(token, chat_id)
            if self.cache_service.contains_key(meta, key):
                self.clear_chat(chat_id, token)
            entity = CacheEntity.with_defaults(key, value, INIT_META_CACHE_TTL)
            self.cache_service.put(meta, entity)
            return {"success": True, "message": key}
        except Exception as e:
            self._log_and_raise_error("An error occurred while initializing the chat", e)

    @abstractmethod
    def chat(self, token, chat_id, question, return_object, user_data):
        self.chat_initialized(token, chat_id)

    def clear_chat(self, chat_id, token):
        try:
            self.processor.clear_chat_history(chat_id)
            meta, key = self._get_meta_key(token, chat_id)
            self.cache_service.invalidate(meta, key)
            return {"message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            self._log_and_raise_error("An error occurred while clearing the context", e)

    def update_chat_id(self, token, init_chat_id, update_chat_id):
        meta, key = self._get_meta_key(token, init_chat_id)
        cache_entity = self.cache_service.get(meta, key)
        cache_entity.key = key.replace(init_chat_id, update_chat_id)
        self.cache_service.put(meta, cache_entity)
        chat_messages = self.get_chat_history(init_chat_id)
        history = get_session_history(init_chat_id)
        history.add_messages(chat_messages)

    def chat_initialized(self, token, chat_id) -> bool:
        meta, key = self._get_meta_key(token, chat_id)
        if not self.cache_service.contains_key(meta, key):
            raise Exception(f"{chat_id} is not in initialized requests. Please initialize first.")
        return True

    def get_chat_history(self, chat_id) -> List[BaseMessage]:
        message_history = get_session_history(chat_id)
        return message_history.messages

    @staticmethod
    def _log_and_raise_error(message, exception):
        logger.error(f"{message}: %s", exception, exc_info=True)
        raise APIException(detail=message) from exception

    @staticmethod
    def _get_meta_key(token, chat_id):
        meta = {"token": token}
        meta.update(CacheEntity.dummy().get_meta_by_id(chat_id))
        key = f"{INIT_REQUESTS_PREFIX}_{chat_id}"
        return meta, key
