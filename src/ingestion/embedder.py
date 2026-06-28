from langchain_huggingface import HuggingFaceEmbeddings


def get_embeddings(model_name: str = "all-MiniLM-L6-v2") -> HuggingFaceEmbeddings:
    """
    Local sentence-transformer embeddings — completely free, no API key needed.
    all-MiniLM-L6-v2 is fast on CPU and accurate enough for incident similarity.
    """
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
