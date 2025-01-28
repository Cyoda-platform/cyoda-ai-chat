import cassio
import logging

from langchain_community.chat_message_histories.cassandra import CassandraChatMessageHistory, DEFAULT_TABLE_NAME
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory

from common_utils.config import MEMORY_STORE, CASSANDRA_MEMORY_STORE_KEYSPACE, RESET_MEMORY
from middleware.repository.cassandra.cassandra_connection import CassandraConnection, CASSANDRA

logger = logging.getLogger("django")

store={}

def init_chat_memory():
    if MEMORY_STORE.upper() == CASSANDRA:
        try:
            if RESET_MEMORY.lower() == "true":
                cassio.config.resolve_session().execute(
                    f"DROP TABLE IF EXISTS {CASSANDRA_MEMORY_STORE_KEYSPACE}.{DEFAULT_TABLE_NAME};"
                )
        except Exception as e:
            logging.error(str(e))
            logger.exception("An exception occurred")

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if MEMORY_STORE.upper() == CASSANDRA:
        if session_id not in store:
            store[session_id] = CassandraChatMessageHistory(
                session_id=session_id,
                session=CassandraConnection().get_session(),
                keyspace=CASSANDRA_MEMORY_STORE_KEYSPACE,
            )
        return store[session_id]
    else:
        if session_id not in store:
            store[session_id] = InMemoryChatMessageHistory()
        return store[session_id]