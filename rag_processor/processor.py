import sys
import logging
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

from common_utils.utils import get_env_var
from .chat_history import ChatHistoryService


# Env vars
OPENAI_API_KEY = get_env_var("OPENAI_API_KEY")
DEEPSEEK_API_KEY = get_env_var("DEEPSEEK_API_KEY")
WORK_DIR = get_env_var("WORK_DIR")
GIT_WORK_DIR = get_env_var("GIT_WORK_DIR")
CYODA_AI_CONFIG_GEN_PATH = get_env_var("CYODA_AI_CONFIG_GEN_PATH")
CYODA_AI_REPO_URL = get_env_var("CYODA_AI_REPO_URL")
CYODA_AI_REPO_BRANCH = get_env_var("CYODA_AI_REPO_BRANCH")
ENV = get_env_var("ENV")
INIT_LLM = get_env_var("INIT_LLM")

# Constants
SPLIT_CHUNK_SIZE = 10000
SPLIT_CHUNK_OVERLAP = 200
SPLIT_DOCS_LOAD_K = 10

CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

logger = logging.getLogger('django')


class RagProcessor:

    def __init__(self):
    
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=SPLIT_CHUNK_SIZE, chunk_overlap=SPLIT_CHUNK_OVERLAP
        )
        logger.info("Initializing RagProcessor v1...")
        
    def init_vectorstore(
        self,  path: str, config_docs: List[Dict]
    ):
        try:
            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules["pysqlite3"]
        except ImportError:
            pass
        
        if INIT_LLM == 'openai':
            loader = (
                self._directory_loader(path)
                if ENV.lower() == "local"
                else self._git_loader(path)
            )
            docs = loader.load()
            if config_docs:
                docs.extend(config_docs)
            logger.info("Number of documents loaded: %s", len(docs))
            splits = self.text_splitter.split_documents(docs)
            return Chroma.from_documents(
                documents=splits, embedding=OpenAIEmbeddings()
            )
        else:
            pass

    def process_rag_chain(
        self, vectorstore, llm, qa_system_prompt: str
    ) -> None:
        # Use pysqlite3 for SQLite if it's available
        if INIT_LLM == 'openai':
            retriever = vectorstore.as_retriever(
                search_kwargs={"k": SPLIT_DOCS_LOAD_K}
            )
            logger.info("Number of documents in vectorstore: %s", vectorstore._collection.count())

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
        else:
            pass

    def get_web_docs(self, urls: List[str]) -> List[Dict]:
        web_loader = WebBaseLoader(urls)
        web_docs = web_loader.load()
        return web_docs

    def initialize_llm(self, temperature, max_tokens, model, openai_api_base):
        """Initializes the language model with the OpenAI API key."""
        print("INIT_LLM")
        print(INIT_LLM)
        if INIT_LLM == 'openai':
            llm = ChatOpenAI(
                model=model,
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=openai_api_base,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return llm
        else:
            pass

    def ask_question(
        self, chat_id: str, question: str, chat_history: ChatHistoryService, rag_chain
    ) -> str:
        ai_msg = rag_chain.invoke(
            {
                "input": question,
                "chat_history": chat_history.get_chat_history(chat_id),
            }
        )

        chat_history.add_to_chat_history(chat_id, question, ai_msg["answer"])
        logger.info(ai_msg["answer"])
        return ai_msg["answer"]

    def load_additional_sources(self, vectorstore, urls: List[str]):
        try:
            logger.info("Fetching additional documents: %s", urls)
            docs = self.get_web_docs(urls)
            splits = self.text_splitter.split_documents(docs)
            vectorstore.add_documents(splits)
            vectorstore.persist()
            logger.info("new count = , %s", vectorstore._collection.count())

            return {"answer": "Added additional sources successfully"}
        except Exception as e:
            logger.error(
                "An error occurred during adding additional sources: %s",
                e,
                exc_info=True,
            )
            return {"error": str(e)}

    def _get_prompt_template(self):
        return ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def _get_text_splitter(self):
        return self.text_splitter

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
