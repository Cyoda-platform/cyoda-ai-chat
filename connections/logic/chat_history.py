from langchain.schema import HumanMessage

class ChatHistoryService:
    def __init__(self):
        self.chat_history = {}

    def add_to_chat_history(self, chat_id, question, message):
        if chat_id in self.chat_history:
            self.chat_history[chat_id].extend([HumanMessage(content=question), message])
        else:
            self.chat_history[chat_id] = [HumanMessage(content=question), message]

    def clear_chat_history(self, chat_id):
        if chat_id in self.chat_history:
            del self.chat_history[chat_id]

    def get_chat_history(self, chat_id):
        return self.chat_history.get(chat_id, [])

    def chat_history_exists(self, chat_id):
        return chat_id in self.chat_history
