from typing import Any

from middleware.entity.entity import BaseEntity


class CacheableEntity(BaseEntity):
    key: Any
    ttl: Any = 31536000




