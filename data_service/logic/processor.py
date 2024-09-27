import logging
from typing import Optional

from common_utils.config import (
    LLM_TEMPERATURE_TRINO,
    LLM_MAX_TOKENS_TRINO,
    LLM_MODEL_TRINO,
    TRINO_ENABLED,
    INIT_LLM,
    TRINO_CONNECTION_STRING,
    CYODA_AI_CONFIG_GEN_TRINO_PATH,
    WORK_DIR,
    TRINO_PROMPT_PATH
)
from langchain_community.utilities.sql_database import SQLDatabase

from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService
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
You can do joins only on indexes!
If you have any errors - max retries is 3.
Always return all correct sql queries you used.
{context}"""

logger = logging.getLogger('django')


class TrinoProcessor(RagProcessor):
    """
    Processor for interacting with Trino via LLM and RAG chain.
    """

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
        self.db = self._initialize_database()
        if INIT_LLM.lower() == "true":
            self.agent_executor = self._initialize_agent()

    def _initialize_database(self) -> Optional[SQLDatabase]:
        if TRINO_ENABLED.lower() == "true":
            try:
                return SQLDatabase.from_uri(TRINO_CONNECTION_STRING)
            except Exception as e:
                logger.error("Failed to initialize Trino database: %s", e, exc_info=True)
                return None
        else:
            logger.warning("Trino is not enabled.")
            return None

    def _initialize_agent(self) -> AgentExecutor:
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

        agent = create_tool_calling_agent(self.llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, vectorstore=self.vectorstore
        )
        return agent_executor

    def _get_rules_of_writing_sql_query_tool(self):

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

    def _analyze_schema_and_tables_tool(self):

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

    def _create_run_sql_query_tool(self):
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

    def ask_question_agent(self, chat_id: str, schema_name: str, question: str) -> str:
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
            self.chat_history.add_to_chat_history(chat_id, str(question), str(answer['output']))
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

    def run_query(self, sql_query: str) -> str:
        if not self.db:
            logger.error("Database connection is not initialized.")
            return "Database connection is not initialized."

        try:
            result = self.db.run(sql_query)
            return result
        except Exception as e:
            logger.error("Error running query: %s", e, exc_info=True)
            return str(e)
