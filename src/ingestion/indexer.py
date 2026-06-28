import os
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "../../.chroma_db")


def build_vector_store(
    documents: list[Document],
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    """Embed documents and persist to local Chroma."""
    store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_dir,
    )
    return store


def load_vector_store(
    embeddings: HuggingFaceEmbeddings,
    persist_dir: str = CHROMA_DIR,
) -> Chroma:
    """Load an already-persisted Chroma store from disk."""
    return Chroma(
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
