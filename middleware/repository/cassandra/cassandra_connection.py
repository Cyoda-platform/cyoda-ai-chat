import logging
from cassandra.cluster import Cluster
import cassio
from common_utils.config import (

    CASSANDRA_HOST,
    CASSANDRA_PORT,
    CASSANDRA_VECTOR_STORE_KEYSPACE,

)

logger = logging.getLogger("django")
CASSANDRA = 'CASSANDRA'

class CassandraConnection:
    _instance = None
    _session = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CassandraConnection, cls).__new__(cls)
            logging.info("CassandraConnection instance created.")
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_connection()

    def _initialize_connection(self):
        try:
            cluster = Cluster(contact_points=[CASSANDRA_HOST],
                              port=CASSANDRA_PORT)
            # protocol_version=CASSANDRA_PROTOCOL_VERSION)
            self._session = cluster.connect()
            cassio.init(session=self._session, keyspace=CASSANDRA_VECTOR_STORE_KEYSPACE)
            CassandraConnection._initialized = True
            logging.info("Cassandra connection established and initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Cassandra: {str(e)}")
            raise

    def get_session(self):
        return self._session