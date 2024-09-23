import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List, Dict, Type
from common_utils.utils import expiration_date

class CacheKeys(Enum):
    LOCAL = "local"

@dataclass
class CacheEntity:
    def __init__(self, key: str, value: Any, ttl: int, meta: Any, last_modified: Optional[int] = None,
                 is_dirty: bool = True):
        self.key = key
        self.value = value
        self.meta = meta
        self.ttl = ttl
        self.expiration = expiration_date(ttl)
        self.last_modified = last_modified if last_modified is not None else int(time.time())
        self.is_dirty = is_dirty

    @classmethod
    def empty(cls, key: str, ttl: int):
        return cls(key=key, value={}, ttl=ttl, meta={}, last_modified=int(time.time()), is_dirty=True)


    @classmethod
    def with_meta(cls, key: str, value: Any, ttl: int, meta: Any):
        return cls(key=key, value=value, ttl=ttl, meta=meta, last_modified=int(time.time()), is_dirty=True)


    @classmethod
    def with_defaults(cls, key: str, value: Any, ttl: int):
        return cls(key=key, value=value, ttl=ttl, meta={}, last_modified=int(time.time()), is_dirty=True)


class CachingService(ABC):
    @abstractmethod
    def put(self, entity: CacheEntity) -> bool:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[CacheEntity]:
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def contains_key(self, key: str) -> bool:
        pass

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        pass

    @abstractmethod
    def invalidate_all(self) -> None:
        pass

    @abstractmethod
    def write_back(self, entities: List[CacheEntity]) -> bool:
        pass

    @abstractmethod
    def flush_dirty_entries(self) -> None:
        pass

    @abstractmethod
    def refresh(self, key: str) -> bool:
        pass


class CacheRegistry:
    _services: Dict[str, CachingService] = {}

    @classmethod
    def register(cls, name: str, service_instance: CachingService):
        if not isinstance(service_instance, CachingService):
            raise TypeError(f"{service_instance.__class__.__name__} must be an instance of CachingService")
        cls._services[name] = service_instance

    @classmethod
    def get_service(cls, name: Optional[str] = CacheKeys.LOCAL.value) -> CachingService:
        if name not in cls._services:
            raise ValueError(f"Unknown cache type: {name}")
        return cls._services[name]