from langchain_community.chat_message_histories.cassandra import CassandraChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

from common_utils.config import VECTOR_STORE, CASSANDRA_MEMORY_STORE_KEYSPACE
from middleware.repository.cassandra.cassandra_connection import CassandraConnection, CASSANDRA

store={}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if VECTOR_STORE.upper() == CASSANDRA:
        message_history = CassandraChatMessageHistory(
            session_id=session_id,
            session=CassandraConnection().get_session(),
            keyspace=CASSANDRA_MEMORY_STORE_KEYSPACE,
        )
        return message_history
    else:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]