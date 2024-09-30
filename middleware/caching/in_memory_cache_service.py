import threading
from typing import Optional, List, Any

import logging

from common_utils.utils import now
from middleware.caching.caching_service import CachingService, CacheEntity
from django.core.cache import cache
from middleware.repository.crud_repository import CrudRepository


logger = logging.getLogger('django')

class InMemoryCachingService(CachingService):
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety

    def __new__(cls, repository: CrudRepository, *args, **kwargs):
        logger.info("initializing InMemoryCachingService")
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(InMemoryCachingService, cls).__new__(cls)
                    cls._instance.cache = cache  # Initialize cache storage
                    cls._instance.repository = repository
        return cls._instance

    def __init__(self, *args, **kwargs):
        pass

    def put(self, meta, entity: CacheEntity) -> bool:
        self.cache.set(entity.key, entity)
        self.cache.touch(entity.key, entity.ttl)
        return True

    def get(self, meta: Any, key: str) -> Optional[CacheEntity]:
        return self.cache.get(key)


    def remove(self, key: str) -> bool:
        return self.cache.delete(key)

    def clear(self) -> None:
        self.cache.clear()

    def contains_key(self, meta: Any, key: str) -> bool:
        return self.get(meta, key) is not None

    def invalidate(self, meta: Any, key: str) -> bool:
        return True

    def invalidate_all(self) -> None:
        self.clear()

    def write_back(self, meta, entities: List[CacheEntity]) -> bool:
        for entity in entities:
            if entity.is_dirty:
                entity.is_dirty = False
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