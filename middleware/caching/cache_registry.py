from typing import Dict, Optional

from middleware.caching.caching_service import CachingService, CacheKeys
from middleware.caching.persistent_cache_service import PersistentCachingService
from middleware.repository.crud_repository import CrudRepository
from middleware.caching.in_memory_cache_service import InMemoryCachingService


class CacheRegistry:
    _instance = None
    _services: Dict[str, CachingService] = {}

    def __new__(cls, database_operations: CrudRepository):
        if cls._instance is None:
            cls._instance = super(CacheRegistry, cls).__new__(cls)
            cls._instance.database_operations = database_operations
            cls._instance._initialize_services()
        return cls._instance

    def _initialize_services(self):
        self.register(CacheKeys.LOCAL.value,
                      InMemoryCachingService(repository=None))
        self.register(CacheKeys.PERSISTENT.value,
                      PersistentCachingService(repository=self.database_operations))

    def register(self, name: str, service_instance: CachingService):
        if not isinstance(service_instance, CachingService):
            raise TypeError(f"{service_instance.__class__.__name__} must be an instance of CachingService")
        self._services[name] = service_instance

    def get_service(self, name: Optional[str] = CacheKeys.LOCAL.value) -> CachingService:
        if name not in self._services:
            raise ValueError(f"Unknown cache type: {name}")
        return self._services[name]