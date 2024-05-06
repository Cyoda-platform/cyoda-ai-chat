import os
import sys
import logging
from dotenv import load_dotenv
from typing import List, Dict

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import (
    GitLoader,
    WebBaseLoader,
    DirectoryLoader,
    TextLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from .chat_history import ChatHistoryService

# Load environment variables
load_dotenv()

# Constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORK_DIR = os.getenv("WORK_DIR")
GIT_WORK_DIR = os.getenv("GIT_WORK_DIR")
CYODA_AI_CONFIG_GEN_PATH = os.getenv("CYODA_AI_CONFIG_GEN_PATH")
CYODA_AI_REPO_URL = os.getenv("CYODA_AI_REPO_URL")
CYODA_AI_REPO_BRANCH = os.getenv("CYODA_AI_REPO_BRANCH")
LOCAL = os.getenv("LOCAL")

CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

# Initialize logging
logger = logging.getLogger(__name__)


class RagProcessor:
    def __init__(self):
        logging.info("Initializing RagProcessor...")

    def process_rag_chain(self, llm, qa_system_prompt: str, path: str, config_docs: List[Dict]) -> None:
        # Use pysqlite3 for SQLite if it's available
        try:
            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules["pysqlite3"]
        except ImportError:
            pass
        
        loader = self._directory_loader(path) if os.getenv("LOCAL", "false").lower() == "true" else self._git_loader(path)
        docs = loader.load()
        docs.extend(config_docs)
        logging.info("Number of documents loaded: %s", len(docs))

        text_splitter = self._get_text_splitter()
        splits = text_splitter.split_documents(docs)
        vectorstore = self._get_vector_store(splits)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
        count = vectorstore._collection.count()
        logging.info("Number of documents in vectorstore: %s", count)

        contextualize_q_prompt = self._get_prompt_template()
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain
        )
        return rag_chain

    def get_web_docs(self, urls: List[str]) -> List[Dict]:
        web_loader = WebBaseLoader(urls)
        web_docs = web_loader.load()
        return web_docs

    def initialize_llm(self, temperature, max_tokens, model):
        """Initializes the language model with the OpenAI API key."""
        llm = ChatOpenAI(
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            openai_api_key=OPENAI_API_KEY,
        )
        return llm
    
    def ask_question(self, chat_id: str, question: str, chat_history: ChatHistoryService, rag_chain) -> str:
        ai_msg = rag_chain.invoke(
            {
                "input": question,
                "chat_history": chat_history.get_chat_history(chat_id),
            }
        )

        chat_history.add_to_chat_history(chat_id, question, ai_msg["answer"])
        logging.info(ai_msg["answer"])
        return ai_msg["answer"]

    def _get_prompt_template(self):
        return ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def _get_vector_store(self, splits: List[Dict]) -> Chroma:
        return Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

    def _get_text_splitter(self):
        return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    def _git_loader(self, path: str) -> GitLoader:
        logger.info("Using remote documents")
        return GitLoader(
            repo_path=GIT_WORK_DIR,
            branch=CYODA_AI_REPO_BRANCH,
            clone_url=CYODA_AI_REPO_URL,
            file_filter=lambda file_path: file_path.startswith(
                f"{GIT_WORK_DIR}/{CYODA_AI_CONFIG_GEN_PATH}/{path}"
            ),
        )

    def _directory_loader(self, path: str) -> DirectoryLoader:
        logger.info("Using local documents")
        return DirectoryLoader(
            f"{WORK_DIR}/{CYODA_AI_CONFIG_GEN_PATH}/{path}", loader_cls=TextLoader
        )