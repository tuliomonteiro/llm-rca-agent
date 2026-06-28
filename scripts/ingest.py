"""
Run once to embed all runbooks and past incidents into the local Chroma vector store.
Usage: python scripts/ingest.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from src.ingestion.loader import load_documents, split_documents
from src.ingestion.embedder import get_embeddings
from src.ingestion.indexer import build_vector_store

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


def main():
    print("Loading documents...")
    docs = load_documents(DATA_DIR)
    print(f"  Loaded {len(docs)} documents")

    print("Splitting into chunks...")
    child_chunks, _ = split_documents(docs)
    print(f"  Created {len(child_chunks)} chunks")

    print("Loading embedding model (downloads once, ~90MB)...")
    embeddings = get_embeddings()

    print("Building vector store...")
    store = build_vector_store(child_chunks, embeddings)
    print(f"  Indexed {store._collection.count()} chunks into Chroma")

    print("\nDone! Vector store is ready at .chroma_db/")


if __name__ == "__main__":
    main()
