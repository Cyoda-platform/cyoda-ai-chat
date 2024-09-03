import logging
import base64
# Common utilities
from common_utils.utils import get_env_var
from langchain_community.utilities.sql_database import SQLDatabase

# RAG processor and chat history services
from rag_processor.processor import RagProcessor
from rag_processor.chat_history import ChatHistoryService

# LangChain components
from langchain.agents import AgentExecutor, create_tool_calling_agent, tool
from langchain_core.prompts import ChatPromptTemplate

from trino.dbapi import connect
from trino.auth import BasicAuthentication

CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH = "trino/"
QA_SYSTEM_PROMPT = """You are a Trino expert. Given an input question, 
first create a syntactically correct Trino sql query to run, 
then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, 
query for at most 100 results using the LIMIT clause as per sql.
You can order the results to return the most informative data in the database.
You must query only the columns that are needed to answer the question. 
Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use date('now') function to get the current date, if the question involves "today\
You can do joins only on indexes!
{context}"""

LLM_TEMPERATURE = float(get_env_var("LLM_TEMPERATURE_TRINO"))
LLM_MAX_TOKENS = int(get_env_var("LLM_MAX_TOKENS_TRINO"))
LLM_MODEL = get_env_var("LLM_MODEL_TRINO")
decoded_bytes_user = base64.b64decode(get_env_var("TRINO_USER"))
TRINO_USER = decoded_bytes_user.decode("utf-8")
decoded_bytes_pwd = base64.b64decode(get_env_var("TRINO_PASSWORD"))
TRINO_PASSWORD = decoded_bytes_pwd.decode("utf-8")
TRINO_CONNECTION_PATH=get_env_var("TRINO_CONNECTION_PATH")
TRINO_CONNECTION_STRING = f"trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_CONNECTION_PATH}"
TRINO_HOST=get_env_var("TRINO_HOST")
logger = logging.getLogger('django')

processor = RagProcessor()
# not tread safe - will be replaced in the future
trino_chat_history = {}

connection_string = f"trino://{TRINO_USER}:{TRINO_PASSWORD}@{TRINO_CONNECTION_PATH}"

# Initialize the SQLDatabase with the connection string
db = SQLDatabase.from_uri(connection_string)
        
class TrinoProcessor:
    def __init__(self):
        """
        Initializes the TrinoProcessor instance.
        """
        self.llm = processor.initialize_llm(
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model=LLM_MODEL,
            openai_api_base=None,
        )
        
        logger.info("LOADING DOCS FOR IMPORT CONFIG")
        self.vectorstore = processor.init_vectorstore(
            CYODA_AI_CONFIG_GEN_CONNECTIONS_PATH, None
        )
        self.rag_chain = processor.process_rag_chain(
            self.vectorstore, self.llm, QA_SYSTEM_PROMPT
        )
        self.chat_history = ChatHistoryService(trino_chat_history)

        
        # Dynamically define tools
        @tool
        def run_sql_query(sql_query: str) -> str:
            """Runs SQL query and returns the dataset from the database."""
            try:
                result = db.run(sql_query)
                return result
            except Exception as e:
                return str(e.__cause__)

        @tool
        def generate_trino_sql(question: str, chat_id: str) -> str:
            """Generates trino and cyoda specific SQL query based on the user question"""
            try:
                formatted_question = f"{question}. Remove any ; (semi colon) at the end"
                sql_query = self.ask_question(chat_id, formatted_question)
                return sql_query
            except Exception as e:
                return str(e.__cause__)
            
        @tool
        def answer_general_question(question: str, chat_id: str) -> str:
            """Answer any question. Should be used to answer any non-specific question as it has chat history"""
            try:
                formatted_question = f"{question}. Remove any ; (semi colon) at the end"
                answer = self.ask_question(chat_id, formatted_question)
                return answer
            except Exception as e:
                return str(e.__cause__)
            
        @tool
        def generate_pandas_ai_compatible_dataset(question: str, chat_id: str) -> str:
            """Formulates pandas compatible dataset"""
            try:
                formatted_question = f"{question}. Return dataset in pandas compatible format. Return only the dataset without any comments or additional text."
                answer = self.ask_question(chat_id, formatted_question)
                return answer
            except Exception as e:
                return str(e.__cause__)

        # Create tool instances
        tools = [run_sql_query, generate_trino_sql, answer_general_question, generate_pandas_ai_compatible_dataset]
        self.llm.bind_tools(tools)
        # Define the agent's prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful assistant. Make sure to use the generate_trino_sql tool to formulate the query. As it is trino and cyoda specific. Make sure there is no semi-colon at the end of the query. Retry up to 2 times if necessary.",
                ),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        # Construct the Tools agent
        agent = create_tool_calling_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, vectorstore=self.vectorstore)

    def ask_question_agent(self, chat_id, question):
        """
        Asks a question using the RAG chain and returns the answer.

        Args:
            chat_id (str): The ID of the chat session.
            question (str): The question to ask.

        Returns:
            str: The answer to the question.
        """
                
        answer = self.agent_executor.invoke({"input": f"{question}. Please use chat_id '{chat_id}'. If you get error, fix the query, explain how you fixed it and retry after correcting the query. Max retries = 3"})
        self.ask_question(chat_id, f"Remeber the results of sql execution: {answer['output']}" )
        return answer['output']

    def ask_question(self, chat_id, question):
        """
        Internal method to handle the RAG chain question asking.
        """
        sql_query = processor.ask_question(chat_id, question, self.chat_history, self.rag_chain)
        return sql_query
    
    def run_query(self, sql_query):
        try:
            result = db.run(sql_query)
            return result
        except Exception as e:
            return str(e.__cause__)