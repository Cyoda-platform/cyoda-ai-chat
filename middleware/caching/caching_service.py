from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, List

from middleware.entity.cache_entity import CacheEntity
from middleware.entity.cacheable_entity import CacheableEntity


class CacheKeys(Enum):
    LOCAL = "LOCAL",
    PERSISTENT = "PERSISTENT"


class CachingService(ABC):
    @abstractmethod
    def put_and_write_back(self, meta: Any, entity: CacheableEntity) -> bool:
        pass

    @abstractmethod
    def put(self, meta: Any, entity: CacheableEntity) -> bool:
        pass

    @abstractmethod
    def get(self, meta: Any, key: str) -> Optional[CacheableEntity]:
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def contains_key(self, meta: Any, key: str) -> bool:
        pass

    @abstractmethod
    def invalidate(self, meta: Any, keys: List[str]) -> bool:
        pass

    @abstractmethod
    def invalidate_all(self) -> None:
        pass

    @abstractmethod
    def write_back(self, meta: Any, entities: List[CacheableEntity]) -> bool:
        pass

    @abstractmethod
    def flush_dirty_entries(self, meta: Any) -> None:
        pass

    @abstractmethod
    def refresh(self, meta: Any, key: str) -> bool:
        pass
