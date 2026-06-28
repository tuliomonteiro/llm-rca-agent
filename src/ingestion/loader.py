from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


def load_documents(data_dir: str) -> list[Document]:
    """Load all .txt and .md files from the given directory tree."""
    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    docs = []
    for file in path.rglob("*"):
        if file.suffix in (".md", ".txt"):
            loader = TextLoader(str(file), encoding="utf-8")
            docs.extend(loader.load())
    return docs


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> tuple[list[Document], list[Document]]:
    """
    Return (child_chunks, parent_chunks) for Parent Document Retrieval.
    Child chunks are small for precise retrieval; parents carry full context.
    """
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    # Parents are larger — LLM gets richer context after retrieval
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size * 4,
        chunk_overlap=chunk_overlap,
    )

    child_chunks = child_splitter.split_documents(documents)
    parent_chunks = parent_splitter.split_documents(documents)

    return child_chunks, parent_chunks
