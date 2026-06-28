"""
Quick smoke test — runs one incident through the full chain and prints the RCA.
Usage: python scripts/run_example.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from src.ingestion.embedder import get_embeddings
from src.ingestion.indexer import load_vector_store
from src.retrieval.retriever import build_retriever
from src.chain.rca_chain import build_rca_chain, get_llm
import json

SAMPLE_INCIDENT = """
Service: auth-api
Environment: production
Start time: 2024-06-10 11:45 UTC
Duration: ~15 minutes

Symptoms:
- HTTP 503 errors on all /login and /token endpoints
- Error logs: "FATAL: remaining connection slots are reserved for non-replication superuser connections"
- Database CPU normal, disk normal
- Spike in active DB connections visible in Datadog just before failure

Recent changes:
- Deployed auth-api v3.1.0 at 11:30 UTC (15 minutes before incident)
- Change included a new "session audit" background thread
"""

def main():
    print("Loading vector store...")
    embeddings = get_embeddings()
    vector_store = load_vector_store(embeddings)

    print("Building chain...")
    llm = get_llm()
    retriever = build_retriever(vector_store, llm, use_compression=False)
    chain = build_rca_chain(retriever, llm)

    print("Running RCA...\n")
    result = chain.invoke(SAMPLE_INCIDENT)
    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
