import os
import sys
import logging
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import GitLoader, WebBaseLoader, DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from .chat_history import ChatHistoryService

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
WORK_DIR = os.environ["WORK_DIR"]
CYODA_AI_REPO_URL = os.environ["CYODA_AI_REPO_URL"]
CYODA_AI_REPO_BRANCH = os.environ["CYODA_AI_REPO_BRANCH"]
CYODA_AI_CONFIG_GEN_MAPPINGS_PATH = os.environ["CYODA_AI_CONFIG_GEN_MAPPINGS_PATH"]

CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""
QA_SYSTEM_PROMPT = """You are a mapping tool. You should do your best to answer the question.
        Use the following pieces of retrieved context to answer the question. \

        {context}"""

# Initialize logging
logging.basicConfig(level=logging.INFO)


class EDMProcessor:
    def __init__(self):
        logging.info("Initializing...")

        # Use pysqlite3 for SQLite if it's available
        try:
            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules["pysqlite3"]
        except ImportError:
            pass
        self.llm = self.initialize_llm()
        loader = self.directory_loader()
        docs = loader.load()
        scripting_docs = self.get_web_script_docs()
        docs.extend(scripting_docs)
        logging.info("Number of documents loaded: %s", len(docs))

        text_splitter = self.get_text_splitter()
        splits = text_splitter.split_documents(docs)
        vectorstore = self.get_vector_store(splits)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        count = vectorstore._collection.count()
        logging.info("Number of documents in vectorestore: %s", count)

        contextualize_q_prompt = self.get_prompt_template()
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", QA_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )
        self.chat_history = ChatHistoryService()

        logging.info("Initialization complete")

    def get_web_script_docs(self):
        web_loader = WebBaseLoader(["https://docs.oracle.com/javase/8/docs/technotes/guides/scripting/prog_guide/javascript.html"])
        scripting_docs = web_loader.load()
        return scripting_docs

    def initialize_llm(self):
        """Initializes the language model with the OpenAI API key."""
        llm = ChatOpenAI(
            temperature=0,
            max_tokens=6000,
            model="gpt-3.5-turbo-16k",
            openai_api_key=OPENAI_API_KEY,
        )
        return llm

    def get_prompt_template(self):
        return ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def get_vector_store(self, splits):
        return Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    def get_text_splitter(self):
        return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    def git_loader(self):
        return GitLoader(
            #clone_url=CYODA_AI_REPO_URL,
            repo_path=WORK_DIR,
            branch=CYODA_AI_REPO_BRANCH,
            file_filter=lambda file_path: file_path.startswith(
                f"{WORK_DIR}/{CYODA_AI_CONFIG_GEN_MAPPINGS_PATH}"
            ),
        )
        
    def directory_loader(self):
        return DirectoryLoader(f"{WORK_DIR}/{CYODA_AI_CONFIG_GEN_MAPPINGS_PATH}", loader_cls=TextLoader)

    def ask_question(self, chat_id, question):
        ai_msg = self.rag_chain.invoke(
            {
                "input": question,
                "chat_history": self.chat_history.get_chat_history(chat_id),
            }
        )

        self.chat_history.add_to_chat_history(chat_id, question, ai_msg["answer"])
        logging.info(ai_msg["answer"])
        return ai_msg["answer"]
