from abc import abstractmethod
from middleware.entity.entity import BaseEntity


class CacheableEntity(BaseEntity):
    @abstractmethod
    def get_key(self):
        pass

    @abstractmethod
    def get_ttl(self):
        pass





