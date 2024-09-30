from common_utils.config import CACHE_STORE, CACHE_DB
from middleware.caching.caching_service import CachingService, CacheKeys
from middleware.caching.in_memory_cache_service import InMemoryCachingService
from middleware.caching.persistent_cache_service import PersistentCachingService
from middleware.repository.repository_registry import RepositoryRegistry

def get_caching_service() -> CachingService:
    if CACHE_STORE.upper() == CacheKeys.PERSISTENT.value:
        repository = RepositoryRegistry().get_service(CACHE_DB)
        return PersistentCachingService(repository=repository)
    else:
        return InMemoryCachingService(repository=None)