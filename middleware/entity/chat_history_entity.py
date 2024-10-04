from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Any, Dict, List

from websockets.utils import generate_key

from common_utils.utils import now, timestamp_before
from middleware.entity.cache_entity import CacheEntity
from middleware.entity.cacheable_entity import CacheableEntity
from middleware.entity.cyoda_entity import CyodaEntity


chat_history_entity_prefix= "chat_history_entity"

@dataclass
class ChatHistoryMessage:
    question: str
    answer: str
    return_object: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ChatHistoryEntity(CacheableEntity, CyodaEntity):
    technical_id: Any = field(init=False, default=None, repr=False, metadata={"include_in_dict": False})
    key: Any
    date: Any
    timestamp: Any
    messages: List[ChatHistoryMessage]
    is_dirty: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'ChatHistoryEntity':
        # Create an instance using data
        entity = cls(
            key=data.get('key', None),
            date=data.get('date', None),
            timestamp=data.get('timestamp', None),
            messages=[
                ChatHistoryMessage(
                    question=msg.get('question', ''),
                    answer=msg.get('answer', ''),
                    return_object=msg.get('return_object', '')
                )
                for msg in data.get('messages', [])
            ],
            is_dirty=data.get('is_dirty', True)
        )
        entity.technical_id = data.get('technical_id', None)
        return entity

    def add_message(self, question: str, answer: str, return_object: str):
        chat_history_message = ChatHistoryMessage(question=question, answer=answer, return_object=return_object)
        self.messages.append(chat_history_message)

    @staticmethod
    def generate_key(key: str):
        return f"{chat_history_entity_prefix}_{key}"

    @staticmethod
    def dummy():
        return ChatHistoryEntity(key="", date="", timestamp=0, messages=[], is_dirty=True)

    @staticmethod
    def empty(key: str):
        current_date = datetime.now().strftime('%Y-%m-%d')
        return ChatHistoryEntity(
            key=key,
            date=str(current_date),
            timestamp=now(),
            messages=[],  # Empty list of messages
            is_dirty=True  # Mark as dirty
        )

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
                    "jsonPath": "$.timestamp",
                    "operatorType": "GREATER_OR_EQUAL",
                    "value": timestamp_before(432000),
                    "type": "simple"
                }
            ],
            "type": "group"
        }
        return condition


    def get_cyoda_meta(self):
        return {"entity_model": "chat_history_entity",
                "entity_version": "1",
                "update_transition": "invalidate"}

    def get_meta(self):
        meta = {}
        meta.update(self.get_cyoda_meta())
        return meta

    def get_meta_by_id(self, key):
        meta = self.get_meta()
        key = self.generate_key(key)
        meta.update({"get_by_id_condition": self.get_by_id_condition(key)})
        return meta


