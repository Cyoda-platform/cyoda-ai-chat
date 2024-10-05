import logging
from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import BaseMessage

from middleware.entity.cache_entity import CacheEntity
from middleware.entity.chat_history_entity import chat_history_entity_prefix, ChatHistoryEntity, ChatHistoryMessage
from rag_processor.caching_service_factory import get_caching_service
from rag_processor.chat_memory_factory import get_session_history
from rag_processor.processor import RagProcessor

logger = logging.getLogger("django")
INIT_REQUESTS_PREFIX = "init"
INIT_META_CACHE_TTL = 31536000


class ConfigInteractor(ABC):

    def __init__(self, processor: RagProcessor):
        self.processor = processor
        self.cache_service = get_caching_service()

    def initialize_chat(self, token, chat_id, value):
        try:
            if self.chat_initialized(token, chat_id):
                self.clear_chat(token, chat_id)
            entity = CacheEntity.with_defaults(chat_id, value, INIT_META_CACHE_TTL)
            meta = self._get_cache_meta(token, chat_id, CacheEntity)
            self.cache_service.put_and_write_back(meta, entity)
            return {"success": True, "message": chat_id}
        except Exception as e:
            raise e

    @abstractmethod
    def chat(self, token, chat_id, question, return_object, user_data):
        self.is_chat_initialized_helper(token, chat_id)

    def clear_chat(self, token, chat_id):
        self.is_chat_initialized_helper(token, chat_id)
        try:
            self.processor.clear_chat_history(chat_id)
            meta = self._get_cache_meta(token, chat_id, CacheEntity)
            self.cache_service.invalidate(meta, [chat_id])

            key = ChatHistoryEntity.generate_key(chat_id)
            meta = self._get_cache_meta(token, key, ChatHistoryEntity)
            if self.cache_service.contains_key(meta, key):
                self.cache_service.invalidate(meta, [key])
            return {"success": True, "message": f"Chat context with id {chat_id} cleared."}
        except Exception as e:
            raise e

    def update_chat_id(self, token, init_chat_id, update_chat_id):
        self._check_update_chat_integrity(token, update_chat_id)

        self.is_chat_initialized_helper(token, init_chat_id)

        meta = self._get_cache_meta(token, init_chat_id, CacheEntity)
        init_cache_entity = self.cache_service.get(meta, init_chat_id)
        update_cache_entity = init_cache_entity
        update_cache_entity.key = update_chat_id
        update_cache_entity.is_dirty = True
        update_meta = self._get_cache_meta(token, update_chat_id, CacheEntity)
        self.cache_service.put_and_write_back(update_meta, update_cache_entity)

        init_chat_history = self.get_chat_history(token, init_chat_id)
        update_chat_history = get_session_history(update_chat_id)
        update_chat_history.add_messages(init_chat_history)

        init_user_chat_history = self.get_user_chat_history(token, init_chat_id)
        update_key = ChatHistoryEntity.generate_key(update_chat_id)
        meta = self._get_cache_meta(token, update_key, ChatHistoryEntity)
        update_user_chat_history = init_user_chat_history
        update_user_chat_history.key = update_key
        update_user_chat_history.is_dirty = True
        self.cache_service.put_and_write_back(meta, update_user_chat_history)

    def _check_update_chat_integrity(self, token, update_chat_id):
        meta = self._get_cache_meta(token, update_chat_id, CacheEntity)
        update_cache_entity = self.cache_service.get(meta, update_chat_id)
        if (update_cache_entity is not None):
            raise Exception(f"update id {update_chat_id} data integrity exception")
        update_chat_history = self.get_chat_history(token, update_chat_id)
        if (update_chat_history is not None and update_chat_history):
            raise Exception(f"update id {update_chat_id} data integrity exception")
        update_user_chat_history = self.get_user_chat_history(token, update_chat_id)
        if (update_user_chat_history is not None and update_user_chat_history):
            raise Exception(f"update id {update_chat_id} data integrity exception")

    def chat_initialized(self, token, chat_id) -> bool:
        meta = self._get_cache_meta(token, chat_id, CacheEntity)
        if not self.cache_service.contains_key(meta, chat_id):
            return False
        return True

    def get_chat_history(self, token, chat_id) -> List[BaseMessage]:
        message_history = get_session_history(chat_id)
        return message_history.messages

    def get_user_chat_history(self, token, chat_id) -> ChatHistoryEntity:
        key = ChatHistoryEntity.generate_key(chat_id)
        meta = self._get_cache_meta(token, key, ChatHistoryEntity)
        message_history = self.cache_service.get(meta, key)
        return message_history

    def add_user_chat_hitory(self, token, chat_id, question, answer, return_object):
        user_chat_history = self.get_user_chat_history(token, chat_id)
        key = ChatHistoryEntity.generate_key(chat_id)
        if user_chat_history:
            user_chat_history.is_dirty = True
            user_chat_history.add_message(ChatHistoryMessage(question, answer, return_object))
        else:
            user_chat_history = ChatHistoryEntity.empty(key)
            user_chat_history.add_message(ChatHistoryMessage(question, answer, return_object))
        meta = self._get_cache_meta(token, key, ChatHistoryEntity)
        self.cache_service.put(meta, user_chat_history)

    def save_chat(self, token, chat_id):
        key = ChatHistoryEntity.generate_key(chat_id)
        meta = self._get_cache_meta(token, key, ChatHistoryEntity)
        user_chat_history = self.cache_service.get(meta, key)
        self.cache_service.write_back(meta, [user_chat_history])

    def is_chat_initialized_helper(self, token, chat_id) -> bool:
        initialized = self.chat_initialized(token, chat_id)
        if not initialized:
            raise Exception(f"{chat_id} is not in initialized requests. Please initialize first.")
        return True

    def _get_user_chat_history_helper(self, token, chat_id):
        meta = self._get_cache_meta(token, chat_id, ChatHistoryEntity)
        if not self.cache_service.contains_key(meta, chat_id):
            return None
        user_chat_history = self.cache_service.get(meta, chat_id)
        return user_chat_history

    @staticmethod
    def _get_cache_meta(token, chat_id, entity):
        meta = {"token": token}
        meta.update(entity.dummy().get_meta_by_id(chat_id))
        return meta
