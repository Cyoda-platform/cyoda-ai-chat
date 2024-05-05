from langchain.schema import HumanMessage

class ChatHistoryService:
    """
    A class to manage chat history for a chat service.

    ...

    Attributes
    ----------
    chat_history : dict
        a dictionary to store chat history, where keys are chat IDs and values are lists of messages

    Methods
    -------
    add_to_chat_history(chat_id, question, message):
        Adds a question and a message to the chat history for a given chat ID.

    clear_chat_history(chat_id):
        Clears the chat history for a given chat ID.

    get_chat_history(chat_id):
        Retrieves the chat history for a given chat ID.

    chat_history_exists(chat_id):
        Checks if chat history exists for a given chat ID.
    """

    def __init__(self, chat_history):
        """
        Constructs all the necessary attributes for the ChatHistoryService object.

        Parameters
        ----------
            chat_history : dict
                a dictionary to store chat history, where keys are chat IDs and values are lists of messages
        """
        self.chat_history = chat_history

    def add_to_chat_history(self, chat_id, question, message):
        """
        Adds a question and a message to the chat history for a given chat ID.

        Parameters
        ----------
            chat_id : str
                the ID of the chat
            question : str
                the question asked by the user
            message : HumanMessage
                the message to be added to the chat history
        """
        if chat_id in self.chat_history:
            self.chat_history[chat_id].extend([HumanMessage(content=question), message])
        else:
            self.chat_history[chat_id] = [HumanMessage(content=question), message]

    def clear_chat_history(self, chat_id):
        """
        Clears the chat history for a given chat ID.

        Parameters
        ----------
            chat_id : str
                the ID of the chat
        """
        if chat_id in self.chat_history:
            del self.chat_history[chat_id]

    def get_chat_history(self, chat_id):
        """
        Retrieves the chat history for a given chat ID.

        Parameters
        ----------
            chat_id : str
                the ID of the chat

        Returns
        -------
        list
            a list of messages in the chat history for the given chat ID, or an empty list if no history exists
        """
        return self.chat_history.get(chat_id, [])

    def chat_history_exists(self, chat_id):
        """
        Checks if chat history exists for a given chat ID.

        Parameters
        ----------
            chat_id : str
                the ID of the chat

        Returns
        -------
        bool
            True if chat history exists for the given chat ID, False otherwise
        """
        return chat_id in self.chat_history