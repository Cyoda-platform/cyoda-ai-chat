import base64
from common_utils.utils import get_env_var

# API Configurations
API_URL = get_env_var("API_URL")
ENV = get_env_var("ENV")
INIT_LLM = get_env_var("INIT_LLM")

# Connection Paths
GET_CONNECTION_CONFIG_PATH = get_env_var("GET_CONNECTION_CONFIG_PATH")
POST_CHECK_CONNECTION_PATH = get_env_var("POST_CHECK_CONNECTION_PATH")
POST_SAVE_DATA_PATH = get_env_var("POST_SAVE_DATA_PATH")
POST_SAVE_SCHEMA_PATH = get_env_var("POST_SAVE_SCHEMA_PATH")

# Working Directory
WORK_DIR = get_env_var("WORK_DIR") if ENV.lower() == "local" else get_env_var("GIT_WORK_DIR")

# JSON Schema Paths
QUESTIONNAIRE_JSON_SCHEMA_PATH = get_env_var("QUESTIONNAIRE_JSON_SCHEMA_PATH_ADD_CONNECTION")
CONNECTION_JSON_SCHEMA_PATH = get_env_var("CONNECTION_JSON_SCHEMA_PATH_ADD_CONNECTION")
ENDPOINT_JSON_SCHEMA_PATH = get_env_var("ENDPOINT_JSON_SCHEMA_PATH_ADD_CONNECTION")
PARAMETER_JSON_SCHEMA_PATH = get_env_var("PARAMETER_JSON_SCHEMA_PATH_ADD_CONNECTION")
IMPORT_CONFIGS_PATH = get_env_var("IMPORT_CONFIGS_PATH_ADD_CONNECTION")
DATASOURCES_CONFIG_SCHEMA_PATH = get_env_var("DATASOURCES_CONFIG_SCHEMA_PATH_ADD_CONNECTION")
WORKFLOW_SCHEMA_PATH = get_env_var("WORKFLOW_SCHEMA_PATH")
WORKFLOW_TRANSITIONS_SCHEMA_PATH = get_env_var("WORKFLOW_TRANSITIONS_SCHEMA_PATH")

# Retries
MAX_RETRIES_ADD_CONNECTION = int(get_env_var("MAX_RETRIES_ADD_CONNECTION"))
MAX_RETRIES_GENERATE_WORKFLOW = int(get_env_var("MAX_RETRIES_GENERATE_WORKFLOW"))

# LLM Configurations
LLM_TEMPERATURE_ADD_CONNECTION = float(get_env_var("LLM_TEMPERATURE_ADD_CONNECTION"))
LLM_MAX_TOKENS_ADD_CONNECTION = int(get_env_var("LLM_MAX_TOKENS_ADD_CONNECTION"))
LLM_MODEL_ADD_CONNECTION = get_env_var("LLM_MODEL_ADD_CONNECTION")

LLM_TEMPERATURE_TRINO = float(get_env_var("LLM_TEMPERATURE_TRINO"))
LLM_MAX_TOKENS_TRINO = int(get_env_var("LLM_MAX_TOKENS_TRINO"))
LLM_MODEL_TRINO = get_env_var("LLM_MODEL_TRINO")

LLM_TEMPERATURE_ADD_SCRIPT = float(get_env_var("LLM_TEMPERATURE_ADD_SCRIPT"))
LLM_MAX_TOKENS_ADD_SCRIPT = int(get_env_var("LLM_MAX_TOKENS_ADD_SCRIPT"))
LLM_MODEL_ADD_SCRIPT = get_env_var("LLM_MODEL_ADD_SCRIPT")

LLM_TEMPERATURE_WORKFLOW = float(get_env_var("LLM_TEMPERATURE_WORKFLOW"))
LLM_MAX_TOKENS_ADD_WORKFLOW = int(get_env_var("LLM_MAX_TOKENS_ADD_WORKFLOW"))
LLM_MODEL_ADD_WORKFLOW = get_env_var("LLM_MODEL_ADD_WORKFLOW")

LLM_TEMPERATURE_CYODA = float(get_env_var("LLM_TEMPERATURE_CYODA"))
LLM_MAX_TOKENS_CYODA = int(get_env_var("LLM_MAX_TOKENS_CYODA"))
LLM_MODEL_CYODA = get_env_var("LLM_MODEL_CYODA")

LLM_TEMPERATURE_RANDOM = float(get_env_var("LLM_TEMPERATURE_RANDOM"))
LLM_MAX_TOKENS_RANDOM = int(get_env_var("LLM_MAX_TOKENS_RANDOM"))
LLM_MODEL_RANDOM = get_env_var("LLM_MODEL_RANDOM")

# Trino Configurations
TRINO_ENABLED = get_env_var("TRINO_ENABLED")
TRINO_PROMPT_PATH = get_env_var("TRINO_PROMPT_PATH")

decoded_bytes_user = base64.b64decode(get_env_var("TRINO_USER"))
TRINO_USER = decoded_bytes_user.decode("utf-8")
decoded_bytes_pwd = base64.b64decode(get_env_var("TRINO_PASSWORD"))
TRINO_PASSWORD = decoded_bytes_pwd.decode("utf-8")
TRINO_CONNECTION_PATH = get_env_var("TRINO_CONNECTION_PATH")
TRINO_CONNECTION_STRING = f"trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_CONNECTION_PATH}"

# Authentication
CYODA_AUTH_ENDPOINT = get_env_var("CYODA_AUTH_ENDPOINT")
ENABLE_AUTH = get_env_var("ENABLE_AUTH")

# API Keys
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
DEEPSEEK_API_KEY = get_env_var("DEEPSEEK_API_KEY")

# Paths
CYODA_AI_CONFIG_GEN_PATH = get_env_var("CYODA_AI_CONFIG_GEN_PATH")
CYODA_AI_REPO_URL = get_env_var("CYODA_AI_REPO_URL")
CYODA_AI_REPO_BRANCH = get_env_var("CYODA_AI_REPO_BRANCH")
CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH = get_env_var("CYODA_AI_CONFIG_GEN_WORKFLOWS_PATH")
WORKFLOW_PROMPT_PATH = get_env_var("WORKFLOW_PROMPT_PATH")
PROMPT_PATH = f"{WORK_DIR}/{WORKFLOW_PROMPT_PATH}"
CYODA_AI_CONFIG_GEN_MAPPINGS_PATH = get_env_var("CYODA_AI_CONFIG_GEN_MAPPINGS_PATH")
CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH = get_env_var("CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH")
CYODA_AI_CONFIG_GEN_TRINO_PATH = get_env_var("CYODA_AI_CONFIG_GEN_TRINO_PATH")
CYODA_AI_CACHE_ENTITY_PATH = get_env_var("CYODA_AI_CACHE_ENTITY_PATH")
CYODA_AI_IMPORT_MODEL_PATH = get_env_var("CYODA_AI_IMPORT_MODEL_PATH")
CYODA_APP_NAME = get_env_var("CYODA_APP_NAME")
CYODA_AI_CONFIG_GEN_CYODA_PATH = get_env_var("CYODA_AI_CONFIG_GEN_CYODA_PATH")
CYODA_AI_CONFIG_GEN_RANDOM_PATH = get_env_var("CYODA_AI_CONFIG_GEN_RANDOM_PATH")

# Chunk Settings
SPLIT_CHUNK_SIZE = int(get_env_var("SPLIT_CHUNK_SIZE"))
SPLIT_CHUNK_OVERLAP = int(get_env_var("SPLIT_CHUNK_OVERLAP"))
SPLIT_DOCS_LOAD_K = int(get_env_var("SPLIT_DOCS_LOAD_K"))
VECTOR_STORE = get_env_var("VECTOR_STORE")
CASSANDRA_HOST = get_env_var("CASSANDRA_HOST")
CASSANDRA_PORT = int(get_env_var("CASSANDRA_PORT"))
CASSANDRA_PROTOCOL_VERSION = int(get_env_var("CASSANDRA_PROTOCOL_VERSION"))
CASSANDRA_VECTOR_STORE_KEYSPACE = get_env_var("CASSANDRA_VECTOR_STORE_KEYSPACE")
CASSANDRA_MEMORY_STORE_KEYSPACE = get_env_var("CASSANDRA_MEMORY_STORE_KEYSPACE")
RESET_RAG_DATA = get_env_var("RESET_RAG_DATA")
RESET_MEMORY = get_env_var("RESET_MEMORY")
CACHE_STORE = get_env_var("CACHE_STORE")
MEMORY_STORE = get_env_var("MEMORY_STORE")
CACHE_DB = get_env_var("CACHE_DB")
