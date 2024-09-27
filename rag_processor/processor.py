import sys
import logging
from abc import ABC
from typing import List, Dict, Optional

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

from common_utils.config import (
    OPENAI_API_KEY,
    CYODA_AI_CONFIG_GEN_PATH,
    CYODA_AI_REPO_URL,
    CYODA_AI_REPO_BRANCH,
    SPLIT_CHUNK_SIZE,
    SPLIT_CHUNK_OVERLAP,
    SPLIT_DOCS_LOAD_K,
    INIT_LLM,
    ENV,
    WORK_DIR,
)
from .chat_history import chat_history_service

CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

logger = logging.getLogger("django")


class RagProcessor(ABC):

    def __init__(
        self,
        temperature: float,
        max_tokens: int,
        model: str,
        openai_api_base: Optional[str],
        path: str,
        config_docs: List[Dict],
        system_prompt: str,
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=SPLIT_CHUNK_SIZE, chunk_overlap=SPLIT_CHUNK_OVERLAP
        )
        logger.info("Initializing RagProcessor v1...")
        self.llm = self.initialize_llm(temperature, max_tokens, model, openai_api_base)
        self.chat_history = chat_history_service
        self.vectorstore = self.init_vectorstore(path, config_docs)
        self.rag_chain = self.process_rag_chain(system_prompt)

    def initialize_llm(
        self,
        temperature: float,
        max_tokens: int,
        model: str,
        openai_api_base: Optional[str],
    ) -> Optional[ChatOpenAI]:
        """Initializes the language model with the OpenAI API key."""
        if INIT_LLM == "true":
            return ChatOpenAI(
                model=model,
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=openai_api_base,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return None

    def init_vectorstore(self, path: str, config_docs: List[Dict]) -> Optional[Chroma]:
        """Initializes the vector store with documents."""
        self._setup_sqlite3()
        if INIT_LLM == "true":
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
            return Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
        return None

    def process_rag_chain(self, qa_system_prompt: str) -> Optional[object]:
        """Processes the RAG chain using the vector store and LLM."""
        if INIT_LLM == "true" and self.vectorstore:
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": SPLIT_DOCS_LOAD_K}
            )
            logger.info(
                "Number of documents in vectorstore: %s",
                self.vectorstore._collection.count(),
            )

            contextualize_q_prompt = self._get_prompt_template()
            history_aware_retriever = create_history_aware_retriever(
                self.llm, retriever, contextualize_q_prompt
            )

            qa_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", qa_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ]
            )
            question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
            return create_retrieval_chain(
                history_aware_retriever, question_answer_chain
            )
        return None

    def get_web_docs(self, urls: List[str]) -> List[Dict]:
        """Loads web documents from provided URLs."""
        web_loader = WebBaseLoader(urls)
        return web_loader.load()

    def get_web_xml_docs(self, urls: List[str]) -> List[Dict]:
        """Loads web XML documents from provided URLs."""
        web_xml_loader = WebBaseLoader(urls)
        web_xml_loader.default_parser = "xml"
        return web_xml_loader.load()

    def ask_rag_question(self, chat_id: str, question: str) -> str:
        """Asks a question using the RAG chain and updates chat history."""
        if self.rag_chain:
            ai_msg = self.rag_chain.invoke(
                {
                    "input": question,
                    "chat_history": self.chat_history.get_chat_history(chat_id),
                }
            )
            self.chat_history.add_to_chat_history(chat_id, question, ai_msg["answer"])
            logger.info(ai_msg["answer"])
            return ai_msg["answer"]
        return ""

    def load_additional_rag_sources(self, urls: List[str]) -> Dict[str, str]:
        """Loads additional documents into the vector store."""
        if self.vectorstore:
            try:
                logger.info("Fetching additional documents: %s", urls)
                xml_urls = [url for url in urls if url.endswith(".xml")]
                other_urls = [url for url in urls if not url.endswith(".xml")]
                docs = self.get_web_docs(other_urls)
                docs.extend(self.get_web_xml_docs(xml_urls))
                splits = self.text_splitter.split_documents(docs)
                self.vectorstore.add_documents(splits)
                self.vectorstore.persist()
                logger.info("New count = %s", self.vectorstore._collection.count())
                return {"answer": "Added additional sources successfully"}
            except Exception as e:
                logger.error(
                    "An error occurred during adding additional sources: %s",
                    e,
                    exc_info=True,
                )
                return {"error": str(e)}
        return {"error": "Vectorstore not initialized."}

    def _get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

    def _setup_sqlite3(self):
        try:
            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules["pysqlite3"]
        except ImportError:
            pass

    def _git_loader(self, path: str) -> GitLoader:
        logger.info("Using remote documents")
        return GitLoader(
            repo_path=WORK_DIR,
            branch=CYODA_AI_REPO_BRANCH,
            clone_url=CYODA_AI_REPO_URL,
            file_filter=lambda file_path: file_path.startswith(
                f"{WORK_DIR}/{CYODA_AI_CONFIG_GEN_PATH}/{path}"
            ),
        )

    def _directory_loader(self, path: str) -> DirectoryLoader:
        logger.info("Using local documents")
        return DirectoryLoader(
            f"{WORK_DIR}/{CYODA_AI_CONFIG_GEN_PATH}/{path}", loader_cls=TextLoader
        )
