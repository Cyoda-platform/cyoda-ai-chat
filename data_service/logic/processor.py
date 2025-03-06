import logging
import threading
import time
from typing import Optional
from urllib.parse import urlparse

import trino
from google.auth import jwt
from langchain.memory import ConversationBufferMemory

from common_utils.config import (
    LLM_TEMPERATURE_TRINO,
    LLM_MAX_TOKENS_TRINO,
    LLM_MODEL_TRINO,
    TRINO_ENABLED,
    INIT_LLM,
    TRINO_CONNECTION_STRING,
    CYODA_AI_CONFIG_GEN_TRINO_PATH,
    WORK_DIR,
    TRINO_PROMPT_PATH, TRINO_CONNECTION_PATH
)
from langchain_community.utilities.sql_database import SQLDatabase

from data_service.logic.custom_trino_auth import CustomJWTAuthentication
from data_service.logic.trino_query_tool import TrinoQueryTool
from rag_processor.chat_memory_factory import get_session_history
from rag_processor.processor import RagProcessor
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_core.prompts import ChatPromptTemplate

QA_SYSTEM_PROMPT = """You are a Trino expert. Given an input question, 
first analyze if it is a general question or it requires interaction with trino. 
If it doesn't require interaction with trino - just answer the question. 
For example if you are asked to provide sql - generate sql, return it, but do not execute it.
Finish.
Else if you need interation with trino: 
First analyze the required schema and tables. 
Then get the rules of trino sql query writing.
Then create a syntactically correct Trino SQL query to run, 
then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, 
query for at most 100 results using the LIMIT clause as per SQL.
You can order the results to return the most informative data in the database.
Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use date('now') function to get the current date, if the question involves "today".
You can do joins only on indexes and root_id (for root entity indexes will be empty)!
If you have any errors - max retries is 3.
Always return all correct sql queries you used.
{context}"""

MAX_POOL_SIZE = 10
MAX_IDLE_TIME = 86400

logger = logging.getLogger('django')


class TrinoProcessor(RagProcessor):
    """
    Processor for interacting with Trino via LLM and RAG chain.
    """

    def __init___V1(self):
        """
        Initializes the TrinoProcessor instance.
        """
        super().__init__(
            temperature=LLM_TEMPERATURE_TRINO,
            max_tokens=LLM_MAX_TOKENS_TRINO,
            model=LLM_MODEL_TRINO,
            openai_api_base=None,
            path=CYODA_AI_CONFIG_GEN_TRINO_PATH,
            config_docs=[],
            system_prompt=QA_SYSTEM_PROMPT
        )
        logger.info("Loading documents for import config")
        self.db = self._initialize_database()
        if INIT_LLM.lower() == "true":
            self.agent_executor = self._initialize_agent()

    def _initialize_database_V1(self) -> Optional[SQLDatabase]:
        if TRINO_ENABLED.lower() == "true":
            try:
                return SQLDatabase.from_uri(TRINO_CONNECTION_STRING)
            except Exception as e:
                logger.error("Failed to initialize Trino database: %s", e, exc_info=True)
                return None
        else:
            logger.warning("Trino is not enabled.")
            return None

    def _initialize_agent_V1(self) -> AgentExecutor:
        tools = [
            self._create_run_sql_query_tool(),
            #self._create_generate_trino_sql_tool(),
            self._create_answer_general_question_tool(),
            #self._create_generate_pandas_dataset_tool(),
            self._analyze_schema_and_tables_tool(),
            self._get_rules_of_writing_sql_query_tool()
        ]
        self.llm.bind_tools(tools)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system",
                 "You are a helpful assistant. Make sure to use the generate_trino_sql tool to formulate the query, as it is Trino and Cyoda specific. Ensure there is no semicolon at the end of the query. Retry up to 2 times if necessary."),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, vectorstore=self.vectorstore, memory=memory,
        )
        return agent_executor

    def _get_rules_of_writing_sql_query_tool_V1(self):

        @tool
        def get_rules_of_writing_sql_query(question: str) -> str:
            """Returns the rules of writing trino specific query. Use it to understand how to write efficient queries."""
            if not self.db:
                return "Database connection is not initialized."
            prompt_path = f"{WORK_DIR}/{TRINO_PROMPT_PATH}"
            try:
                with open(prompt_path, "r") as file:
                    prompt = file.read()
            except FileNotFoundError as e:
                return str(e.__cause__)
            return prompt

        return get_rules_of_writing_sql_query

    def _analyze_schema_and_tables_tool_V1(self):

        @tool
        def analyze_schema_and_tables(schema_name: str) -> str:
            """Returns schema structure and tables structure. You need this tool to know what data is stored in the tables in order to generate a correct query."""
            if not self.db:
                return "Database connection is not initialized."
            try:
                sql_query = f"SELECT * FROM information_schema.columns WHERE table_schema = '{schema_name}' AND column_name != 'id' AND column_name != 'root_id' AND column_name != 'parent_id'"
                result = self.db.run(sql_query)
                return result
            except Exception as e:
                return str(e.__cause__)

        return analyze_schema_and_tables

    def _create_run_sql_query_tool_V1(self):
        @tool
        def run_sql_query(sql_query: str) -> str:
            """Runs SQL query and returns the dataset from the database."""
            if not self.db:
                return "Database connection is not initialized."
            try:
                result = self.db.run(sql_query)
                return result
            except Exception as e:
                logger.error("Error executing SQL query: %s", e, exc_info=True)
                return str(e)

        return run_sql_query

    #def _create_generate_trino_sql_tool(self):
    #    @tool
    #    def generate_trino_sql(question: str, chat_id: str) -> str:
    #        """Generates Trino and Cyoda-specific SQL query based on the user question."""
    #        try:
    #            formatted_question = f"{question}. Remove any ; (semicolon) at the end"
    #            sql_query = self.ask_question(chat_id, formatted_question)
    #            return sql_query
    #        except Exception as e:
    #            logger.error("Error generating Trino SQL: %s", e, exc_info=True)
    #            return str(e)

    #    return generate_trino_sql

    def _create_answer_general_question_tool(self):
        @tool
        def answer_general_question(question: str, chat_id: str) -> str:
            """Answers any question using chat history."""
            try:
                formatted_question = f"{question}. Remove any ; (semicolon) at the end"
                answer = self.ask_question(chat_id, formatted_question)
                return answer
            except Exception as e:
                logger.error("Error answering general question: %s", e, exc_info=True)
                return str(e)

        return answer_general_question

    def _create_generate_pandas_dataset_tool(self):
        @tool
        def generate_pandas_ai_compatible_dataset(question: str, chat_id: str) -> str:
            """Formulates pandas-compatible dataset."""
            try:
                formatted_question = f"{question}. Return dataset in pandas-compatible format. Return only the dataset without any comments or additional text."
                answer = self.ask_question(chat_id, formatted_question)
                return answer
            except Exception as e:
                logger.error("Error generating pandas dataset: %s", e, exc_info=True)
                return str(e)

        return generate_pandas_ai_compatible_dataset

    def ask_question_agent_V1(self, chat_id: str, schema_name: str, question: str) -> str:
        if not hasattr(self, 'agent_executor'):
            logger.error("Agent executor is not initialized.")
            return "Agent executor is not initialized."

        input_prompt = (
            f"{question}. Schema name is '{schema_name}'. Please use chat_id '{chat_id}'. Analyze the table structure first and check the rules for writing query."
            f" Remember the rules how to formulate queries specific to cyoda trino. Remember what tables structure do you have, maybe you need joins. Remember how to do joins."
            f"If you get an error, fix the query, explain how you fixed it, and retry after correcting the query. Return the answer to the question. Max retries = 3."
            f"Always include all successful sql queries into the answer"
        )
        try:
            answer = self.agent_executor.invoke({"input": input_prompt})
            return answer['output']
        except Exception as e:
            logger.error("Error in ask_question_agent: %s", e, exc_info=True)
            return str(e)

    def ask_question(self, chat_id: str, question: str) -> str:
        try:
            sql_query = self.ask_rag_question(chat_id, question)
            return sql_query
        except Exception as e:
            logger.error("Error in ask_question: %s", e, exc_info=True)
            return str(e)

    def run_query_V1(self, sql_query: str) -> str:
        if not self.db:
            logger.error("Database connection is not initialized.")
            return "Database connection is not initialized."

        try:
            result = self.db.run(sql_query)
            return result
        except Exception as e:
            logger.error("Error running query: %s", e, exc_info=True)
            return str(e)


    def __init__(self):
        """
        Initializes the TrinoProcessor instance.
        """
        super().__init__(
            temperature=LLM_TEMPERATURE_TRINO,
            max_tokens=LLM_MAX_TOKENS_TRINO,
            model=LLM_MODEL_TRINO,
            openai_api_base=None,
            path=CYODA_AI_CONFIG_GEN_TRINO_PATH,
            config_docs=[],
            system_prompt=QA_SYSTEM_PROMPT
        )
        logger.info("Loading documents for import config")
        self.connection_pool = {}  # {connection_string: (SQLDatabase, last_used_timestamp)}
        self.connection_lock = threading.Lock()
        self.agent_lock = threading.Lock()
        self.max_pool_size = MAX_POOL_SIZE
        self.max_idle_time = MAX_IDLE_TIME  # Connections older than this will be removed
        self.agent_pool = {}  # {connection_string: (AgentExecutor, last_used_timestamp)}

    def get_username(self, token):
        if token.startswith("Bearer "):
            token = token[7:]
        decoded = jwt.decode(token, verify=False)
        username = decoded.get("sub")
        return username

    def get_database(self, token, trino_host) -> Optional[TrinoQueryTool]:
        """
        Retrieves a database connection from the pool or creates a new one if necessary.
        If the pool limit is reached, it removes the least recently used connection.
        """
        if TRINO_ENABLED.lower() == "true":
            current_time = time.monotonic()
            username = self.get_username(token)
            username_trinohost = f"{username}_{trino_host}"

            # Check if connection already exists **without lock**
            db_entry = self.connection_pool.get(username_trinohost)
            if db_entry:
                self.connection_pool[username_trinohost] = (db_entry[0], current_time)
                return db_entry[0]

            with self.connection_lock: # Lock only when modifying the pool
                self._cleanup_connections(current_time)

                if username_trinohost in self.connection_pool:
                    self.connection_pool[username_trinohost] = (self.connection_pool[username_trinohost][0], current_time)
                    return self.connection_pool[username_trinohost][0]

                if len(self.connection_pool) >= self.max_pool_size:
                    oldest_key = min(self.connection_pool, key=lambda k: self.connection_pool[k][1])
                    logger.info(f"Removing least used connection: {oldest_key}")
                    del self.connection_pool[oldest_key]

                try:
                    logger.info(f"Creating new connection for {username_trinohost}")
                    port, catalog, schema = TRINO_CONNECTION_PATH.split('/')
                    parsed_trino_host = urlparse(trino_host)
                    http_scheme = parsed_trino_host.scheme
                    host = parsed_trino_host.hostname
                    trino_conn = trino.dbapi.connect(
                        host=f"trino-{host}",
                        port=int(port),
                        http_scheme=http_scheme,
                        auth=CustomJWTAuthentication(token),
                        catalog=catalog,
                        schema=schema,
                    )

                    db = TrinoQueryTool(trino_conn)
                    self.connection_pool[username_trinohost] = (db, current_time)
                    return db
                except Exception as e:
                    logger.error(f"Failed to create Trino database connection: {e}", exc_info=True)
                    return None
        else:
            logger.warning("Trino is not enabled.")
            return None

    def _cleanup_connections(self, current_time):
        """
        Removes idle connections that have been unused longer than max_idle_time.
        """
        idle_connections = [key for key, (_, last_used) in self.connection_pool.items()
                            if current_time - last_used > self.max_idle_time]

        for key in idle_connections:
            logger.info(f"Removing idle connection: {key}")
            del self.connection_pool[key]

    def get_agent(self, token: str, trino_host: str) -> Optional[AgentExecutor]:
        """
        Retrieves an agent from the pool or creates a new one if necessary.
        If the pool limit is reached, it removes the least recently used agent.
        """
        current_time = time.monotonic()
        username = self.get_username(token)
        username_trinohost = f"{username}_{trino_host}"

        db = self.get_database(token, trino_host)
        if db is None:
            logger.error(f"Cannot initialize agent, no active database for {username_trinohost}")
            return None

        # Check if agent already exists **without lock**
        agent_entry = self.agent_pool.get(username_trinohost)
        if agent_entry:
            self.agent_pool[username_trinohost] = (agent_entry[0], current_time)
            return agent_entry[0]

        with self.agent_lock: # Lock only when modifying the agent pool
            self._cleanup_agents(current_time)

            if username_trinohost in self.agent_pool:
                self.agent_pool[username_trinohost] = (self.agent_pool[username_trinohost][0], current_time)
                return self.agent_pool[username_trinohost][0]

            if len(self.agent_pool) >= self.max_pool_size:
                oldest_key = min(self.agent_pool, key=lambda k: self.agent_pool[k][1])
                logger.info(f"Removing least used agent: {oldest_key}")
                del self.agent_pool[oldest_key]

            agent = None
            if INIT_LLM.lower() == "true":
                agent = self._initialize_agent(db)
            if agent:
                self.agent_pool[username_trinohost] = (agent, current_time)
            return agent

    def _cleanup_agents(self, current_time):
        """
        Removes idle agents that have been unused longer than max_idle_time.
        """
        idle_agents = [key for key, (_, last_used) in self.agent_pool.items()
                       if current_time - last_used > self.max_idle_time]

        for key in idle_agents:
            logger.info(f"Removing idle agent: {key}")
            del self.agent_pool[key]

    def _initialize_agent(self, db: TrinoQueryTool) -> Optional[AgentExecutor]:
        """
        Initializes an agent instance for a specific Trino connection.
        """
        tools = [
            self._create_run_sql_query_tool(db),
            # self._create_generate_trino_sql_tool(),
            self._create_answer_general_question_tool(),
            # self._create_generate_pandas_dataset_tool(),
            self._analyze_schema_and_tables_tool(db),
            self._get_rules_of_writing_sql_query_tool(db)
        ]
        self.llm.bind_tools(tools)

        prompt = ChatPromptTemplate.from_messages(
                [
                    ("system",
                     "You are a helpful assistant. Make sure to use the generate_trino_sql tool to formulate the query, as it is Trino and Cyoda specific. Ensure there is no semicolon at the end of the query. Retry up to 2 times if necessary."),
                    ("placeholder", "{chat_history}"),
                    ("human", "{input}"),
                    ("placeholder", "{agent_scratchpad}"),
                ]
            )

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, vectorstore=self.vectorstore, memory=memory,
        )
        return agent_executor

    def _get_rules_of_writing_sql_query_tool(self, db):
        @tool
        def get_rules_of_writing_sql_query(question: str) -> str:
            """Returns the rules of writing trino specific query. Use it to understand how to write efficient queries."""
            if not db:
                return "Database connection is not initialized."
            prompt_path = f"{WORK_DIR}/{TRINO_PROMPT_PATH}"
            try:
                with open(prompt_path, "r") as file:
                    prompt = file.read()
            except FileNotFoundError as e:
                return str(e.__cause__)
            return prompt

        return get_rules_of_writing_sql_query

    def _analyze_schema_and_tables_tool(self, db):
        @tool
        def analyze_schema_and_tables(schema_name: str) -> str:
            """Returns schema structure and tables structure. You need this tool to know what data is stored in the tables in order to generate a correct query."""
            if not db:
                return "Database connection is not initialized."
            try:
                sql_query = f"SELECT * FROM information_schema.columns WHERE table_schema = '{schema_name}' AND column_name != 'id' AND column_name != 'root_id' AND column_name != 'parent_id'"
                result = db.run(sql_query)
                return result
            except Exception as e:
                return str(e.__cause__)

        return analyze_schema_and_tables

    def _create_run_sql_query_tool(self, db):
        @tool
        def run_sql_query(sql_query: str) -> str:
            """Runs SQL query and returns the dataset from the database."""
            if not db:
                return "Database connection is not initialized."
            try:
                result = db.run(sql_query)
                return result
            except Exception as e:
                logger.error("Error executing SQL query: %s", e, exc_info=True)
                return str(e)

        return run_sql_query

    def ask_question_agent(self, token: str, trino_host: str, chat_id: str, schema_name: str, question: str) -> str:
        """
        Uses the agent to process a question and generate a Trino SQL query.
        """
        agent = self.get_agent(token, trino_host)
        if not agent:
            return "Agent initialization failed."

        input_prompt = (
            f"{question}. Schema name is '{schema_name}'. Please use chat_id '{chat_id}'. Analyze the table structure first and check the rules for writing query."
            f" Remember the rules how to formulate queries specific to cyoda trino. Remember what tables structure do you have, maybe you need joins. Remember how to do joins."
            f"If you get an error, fix the query, explain how you fixed it, and retry after correcting the query. Return the answer to the question. Max retries = 3."
            f"Always include all successful sql queries into the answer"
        )

        try:
            response = agent.invoke({"input": input_prompt})
            return response.get("output", "No response")
        except Exception as e:
            logger.error(f"Error in ask_question_agent: {e}", exc_info=True)
            return str(e)

    def run_query(self, token: str, trino_host: str, sql_query: str) -> str:
        """
        Runs an SQL query using the appropriate database connection.
        """
        db = self.get_database(token, trino_host)
        if db is None:
            logger.error("Database connection is not initialized.")
            return "Database connection is not initialized."
        try:
            result = db.run_query(sql_query)
            return result
        except Exception as e:
            logger.error("Error executing SQL query: %s", e, exc_info=True)
            return str(e)

