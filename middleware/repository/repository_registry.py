from typing import Dict, Optional

from middleware.repository.cyoda.cyoda_service import CyodaService
from middleware.repository.crud_repository import CrudRepository, DBKeys


class RepositoryRegistry:
    _instance = None
    _services: Dict[str, CrudRepository] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RepositoryRegistry, cls).__new__(cls)
            cls._instance._initialize_services()
        return cls._instance

    def _initialize_services(self):
        self.register(DBKeys.CYODA.value,
                      CyodaService())

    def register(self, name: str, service_instance: CrudRepository):
        if not isinstance(service_instance, CrudRepository):
            raise TypeError(f"{service_instance.__class__.__name__} must be an instance of CachingService")
        self._services[name] = service_instance

    def get_service(self, name: Optional[str] = DBKeys.CYODA.value) -> CrudRepository:
        if name not in self._services:
            raise ValueError(f"Unknown cache type: {name}")
        return self._services[name]