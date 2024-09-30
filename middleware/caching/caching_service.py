from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, List

from middleware.repository.entity.cache_entity import CacheEntity


class CacheKeys(Enum):
    LOCAL = "LOCAL",
    PERSISTENT = "PERSISTENT"


class CachingService(ABC):
    @abstractmethod
    def put(self, meta: Any, entity: CacheEntity) -> bool:
        pass

    @abstractmethod
    def get(self, meta: Any, key: str) -> Optional[CacheEntity]:
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
    def invalidate(self, meta: Any, key: str) -> bool:
        pass

    @abstractmethod
    def invalidate_all(self) -> None:
        pass

    @abstractmethod
    def write_back(self, meta: Any, entities: List[CacheEntity]) -> bool:
        pass

    @abstractmethod
    def flush_dirty_entries(self, meta: Any) -> None:
        pass

    @abstractmethod
    def refresh(self, meta: Any, key: str) -> bool:
        pass
