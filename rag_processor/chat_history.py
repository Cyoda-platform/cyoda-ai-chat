from langchain.schema import HumanMessage

import threading

class ChatHistoryService:
    _instance = None
    _lock = threading.Lock()  # Lock for thread safety

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  # Ensure only one thread can create the instance
                if cls._instance is None:
                    cls._instance = super(ChatHistoryService, cls).__new__(cls)
                    cls._instance.chat_history = {}
        return cls._instance

    def __init__(self):
        # Empty because initialization is done in __new__
        pass

    def add_to_chat_history(self, chat_id, question, message):
        with self._lock:
            if chat_id in self.chat_history:
                self.chat_history[chat_id].extend([HumanMessage(content=question), message])
            else:
                self.chat_history[chat_id] = [HumanMessage(content=question), message]

    def clear_chat_history(self, chat_id):
        with self._lock:
            if chat_id in self.chat_history:
                del self.chat_history[chat_id]

    def get_chat_history(self, chat_id):
        with self._lock:
            return self.chat_history.get(chat_id, [])

    def chat_history_exists(self, chat_id):
        with self._lock:
            return chat_id in self.chat_history

# Create a single instance
chat_history_service = ChatHistoryService()