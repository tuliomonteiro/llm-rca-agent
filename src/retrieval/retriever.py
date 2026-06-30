from langchain_chroma import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.language_models import BaseLanguageModel
from langchain_core.documents import Document


def _deduplicate_by_source(docs: list[Document]) -> list[Document]:
    """Keep only the first chunk per source file to avoid duplicate context."""
    seen = set()
    result = []
    for doc in docs:
        source = doc.metadata.get("source", "")
        if source not in seen:
            seen.add(source)
            result.append(doc)
    return result


def build_retriever(
    vector_store: Chroma,
    llm: BaseLanguageModel,
    k: int = 4,
    use_compression: bool = True,
):
    """
    Build a retriever with optional Contextual Compression.

    Contextual Compression strips irrelevant passages before they reach
    the LLM, reducing token usage and noise — key for incident logs that
    contain lots of metadata unrelated to the actual root cause.

    fetch_k is set higher than k so MMR has enough candidates to both
    maximise relevance and cover diverse sources (e.g. runbooks vs incidents).
    Deduplication by source is applied after retrieval so a single file
    that was indexed in multiple chunks can't consume more than one slot.
    """
    base_retriever = vector_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k * 2, "fetch_k": k * 6},  # fetch more, dedupe down to k
    )

    class DeduplicatingRetriever:
        def __init__(self, retriever, target_k):
            self._retriever = retriever
            self._k = target_k

        def invoke(self, query: str) -> list[Document]:
            docs = self._retriever.invoke(query)
            return _deduplicate_by_source(docs)[: self._k]

    dedup_retriever = DeduplicatingRetriever(base_retriever, k)

    if not use_compression:
        return dedup_retriever

    compressor = LLMChainExtractor.from_llm(llm)
    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )
