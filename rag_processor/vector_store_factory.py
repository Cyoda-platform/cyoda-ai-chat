import logging
from langchain_community.vectorstores import Cassandra
import cassio
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from common_utils.config import (
    VECTOR_STORE,
    CASSANDRA_VECTOR_STORE_KEYSPACE,
    RESET_RAG_DATA
)
from middleware.repository.cassandra.cassandra_connection import CassandraConnection, CASSANDRA

logger = logging.getLogger("django")


def create_vector_store(path, splits):
    try:
        if VECTOR_STORE.upper() == CASSANDRA:
            logging.info("Using existing Cassandra connection...")
            session = CassandraConnection().get_session()
            table_name = f"cassandra_vector_{path}".replace("/", "")
            try:
                if RESET_RAG_DATA.lower() == "true":
                    cassio.config.resolve_session().execute(
                        f"DROP TABLE IF EXISTS {cassio.config.resolve_keyspace()}.{table_name};"
                    )
            except Exception as e:
                logging.error(str(e))
            cassandra = Cassandra(embedding=OpenAIEmbeddings(),
                                  table_name=table_name,
                                  session=session,
                                  keyspace=CASSANDRA_VECTOR_STORE_KEYSPACE)
            if RESET_RAG_DATA.lower() == "true":
                cassandra.add_documents(splits)
            return cassandra

        else:  # Defaults to Chroma
            logging.info("Using Chroma as the vector store.")
            return Chroma.from_documents(
                documents=splits,
                embedding=OpenAIEmbeddings()
            )

    except Exception as e:
        logging.error(f"Error creating vector store: {str(e)}")
        raise
