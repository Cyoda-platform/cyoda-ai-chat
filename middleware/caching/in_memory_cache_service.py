import threading
import time
from typing import Optional, List

import logging
from middleware.caching.caching_service import CachingService, CacheEntity, CacheRegistry, CacheKeys
from django.core.cache import cache

logger = logging.getLogger('django')

class InMemoryCachingService(CachingService):
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(InMemoryCachingService, cls).__new__(cls)
                    cls._instance.cache = cache  # Initialize cache storage
        return cls._instance

    def __init__(self):
        # logger.info() can be placed in __new__ or removed altogether
        pass

    def put(self, entity: CacheEntity) -> bool:
        self.cache.set(entity.key, entity)
        self.cache.touch(entity.key, entity.ttl)
        return True

    def get(self, key: str) -> Optional[CacheEntity]:
        return self.cache.get(key)

    def remove(self, key: str) -> bool:
        return self.cache.delete(key)

    def clear(self) -> None:
        self.cache.clear()

    def contains_key(self, key: str) -> bool:
        return key in self.cache

    def invalidate(self, key: str) -> bool:
        return self.remove(key)

    def invalidate_all(self) -> None:
        self.clear()

    def write_back(self, entities: List[CacheEntity]) -> bool:
        # Simulate write back to the database
        for entity in entities:
            if entity.is_dirty:
                entity.is_dirty = False
        return True

    def flush_dirty_entries(self) -> None:
        dirty_entities = [entity for entity in self.cache.values() if entity.is_dirty]
        self.write_back(dirty_entities)

    def refresh(self, key: str) -> bool:
        entity = self.get(key)
        if entity:
            entity.last_modified = int(time.time())  # Update with current timestamp
            entity.is_dirty = False
            return True
        return False

CacheRegistry.register(CacheKeys.LOCAL.value, InMemoryCachingService())