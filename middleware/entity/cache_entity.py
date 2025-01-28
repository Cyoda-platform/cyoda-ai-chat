from dataclasses import dataclass, asdict, field
from typing import Any

from common_utils.config import CYODA_ENTITY_VERSION
from common_utils.utils import expiration_date, now
from middleware.entity.cacheable_entity import CacheableEntity
from middleware.entity.cyoda_entity import CyodaEntity

CACHE_ENTITY = "cache_entity"


@dataclass
class CacheEntity(CacheableEntity, CyodaEntity):

    technical_id: Any = field(init=False, default=None, repr=False, metadata={"include_in_dict":False})
    key: Any
    value: Any
    meta: Any
    ttl: Any
    expiration: Any
    last_modified: Any
    is_dirty: bool

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'CacheEntity':
        # Create an instance using data
        entity = cls(
            key=data.get('key', None),
            value=data.get('value', None),
            meta=data.get('meta', None),
            ttl=data.get('ttl', None),
            expiration=data.get('expiration', None),
            last_modified=data.get('last_modified', None),
            is_dirty=data.get('is_dirty', True)
        )
        entity.technical_id = data.get('technical_id', None)
        return entity

    def get_key(self):
        return self.key

    def get_ttl(self):
        return self.ttl


    @staticmethod
    def dummy():
        return CacheEntity(key="", value={}, ttl=0, meta={}, expiration=expiration_date(31536000), last_modified=now(), is_dirty=True)

    @staticmethod
    def empty(key: str, ttl: int):
        return CacheEntity(key=key, value={}, ttl=ttl, meta={}, expiration=expiration_date(ttl), last_modified=now(), is_dirty=True)

    @staticmethod
    def with_meta(key: str, value: Any, ttl: int, meta: Any):
        return CacheEntity(key=key, value=value, ttl=ttl, meta=meta, expiration=expiration_date(ttl), last_modified=now(), is_dirty=True)

    @staticmethod
    def with_defaults(key: str, value: Any, ttl: int):
        return CacheEntity(key=key, value=value, ttl=ttl, meta={}, expiration=expiration_date(ttl), last_modified=now(), is_dirty=True)

    @staticmethod
    def generate_id(prefix: str, key: str):
        return f"{prefix}_{key}"

    @staticmethod
    def get_by_id_condition(key: str):
        condition = {
            "operator": "AND",
            "conditions": [
                {
                    "jsonPath": "$.key",
                    "operatorType": "EQUALS",
                    "value": key,
                    "type": "simple"
                },
                {
                    "jsonPath": "$.expiration",
                    "operatorType": "GREATER_OR_EQUAL",
                    "value": now(),
                    "type": "simple"
                }
            ],
            "type": "group"
        }
        return condition


    def get_cyoda_meta(self):
        return {"entity_model": CACHE_ENTITY,
                "entity_version": CYODA_ENTITY_VERSION,
                "update_transition": "invalidate"}

    def get_meta(self):
        meta = {}
        meta.update(self.get_cyoda_meta())
        return meta

    def get_meta_by_id(self, key):
        meta = self.get_meta()
        meta.update({"get_by_id_condition": self.get_by_id_condition(key)})
        return meta


