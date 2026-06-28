from langchain_chroma import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_core.language_models import BaseLanguageModel


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
    """
    base_retriever = vector_store.as_retriever(
        search_type="mmr",  # Max Marginal Relevance — diverse results, less repetition
        search_kwargs={"k": k, "fetch_k": k * 3},
    )

    if not use_compression:
        return base_retriever

    compressor = LLMChainExtractor.from_llm(llm)
    return ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )
