import threading
from typing import Optional, List, Any

import logging

from common_utils.utils import now
from middleware.caching.caching_service import CachingService
from django.core.cache import cache

from middleware.entity.cache_entity import CacheableEntity
from middleware.repository.crud_repository import CrudRepository

logger = logging.getLogger('django')


class PersistentCachingService(CachingService):
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety

    def __new__(cls, repository: CrudRepository, *args, **kwargs):
        logger.info("initializing InMemoryCachingService")
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PersistentCachingService, cls).__new__(cls)
                    cls._instance.cache = cache  # Initialize cache storage
                    cls._instance.repository = repository
        return cls._instance

    def __init__(self, *args, **kwargs):
        pass

    def put_and_write_back(self, meta, entity: CacheableEntity) -> bool:
        self.put(meta, entity)
        self.write_back(meta, [entity])
        return True

    def put(self, meta, entity: CacheableEntity) -> bool:
        self.cache.set(entity.get_key(), entity)
        self.cache.touch(entity.get_key(), entity.get_ttl())
        return True

    def get(self, meta: Any, key: str) -> Optional[CacheableEntity]:
        entity = self.cache.get(key)
        if entity is None:
            entity = self.repository.find_by_key(meta, key)
            if entity is None:
                return None
            self.put(meta, entity)
        return self.cache.get(key)

    def remove(self, key: str) -> bool:
        return self.cache.delete(key)

    def clear(self) -> None:
        self.cache.chat_clear()

    def contains_key(self, meta: Any, key: str) -> bool:
        return self.get(meta, key) is not None

    def invalidate(self, meta: Any, keys: List[str]) -> bool:
        self.cache.delete_many(keys)
        entities = self.repository.find_all_by_key(meta, keys)
        if entities is not None:
            for entity in entities:
                entity.expiration = now()
        self.repository.update_all(meta, entities)
        return True

    def invalidate_all(self) -> None:
        self.clear()

    def write_back(self, meta, entities: List[CacheableEntity]) -> bool:
        for entity in entities:
            if entity.is_dirty:
                entity.is_dirty = False
                self.repository.save_all(meta, entities)
        return True

    def flush_dirty_entries(self, meta) -> None:
        dirty_entities = [entity for entity in self.cache.values() if entity.is_dirty]
        self.write_back(meta, dirty_entities)

    def refresh(self, meta: Any, key: str) -> bool:
        entity = self.get(meta, key)
        if entity:
            entity.last_modified = now()  # Update with current timestamp
            entity.is_dirty = False
            return True
        return False
