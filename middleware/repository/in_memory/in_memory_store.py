from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

class InMemoryHistory(BaseChatMessageHistory):
    _instance = None # Lock for thread safety

    def __new__(cls, session_id, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(InMemoryHistory, cls).__new__(cls)
            cls._instance.session_id = session_id
            cls._instance.history = {}
        return cls._instance


    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        if self.session_id not in self.history:
            return []
        return self.history[self.session_id]

    def add_messages(self, messages: List[BaseMessage]) -> None:
        """Add a list of messages to the store"""
        if self.session_id in self.history:
            self.history[self.session_id].extend(messages)
        else:
            self.history[self.session_id] = messages

    def clear(self) -> None:
        if self.session_id in self.history:
            del self.history[self.session_id]


