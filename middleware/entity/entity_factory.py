from middleware.entity.cache_entity import CACHE_ENTITY, CacheEntity
from middleware.entity.chat_history_entity import CHAT_HISTORY_ENTITY, ChatHistoryEntity


def base_entity_from_dict(entity_model, data):
    if entity_model == CACHE_ENTITY:
        return CacheEntity.from_dict(data)
    elif entity_model == CHAT_HISTORY_ENTITY:
        return ChatHistoryEntity.from_dict(data)
    else:
        raise Exception("no entity registered")