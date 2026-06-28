import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnableLambda
from langchain.schema import Document

from src.parser.output import RCAReport, FallbackReport
from src.chain.prompts import get_rca_prompt, get_fallback_prompt


def _format_docs(docs: list[Document]) -> str:
    if not docs:
        return ""
    return "\n\n---\n\n".join(
        f"[Source: {doc.metadata.get('source', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )


def _sanitize_incident(text: str) -> str:
    """Basic prompt injection guard."""
    injection_patterns = [
        "ignore previous instructions",
        "ignore all instructions",
        "disregard",
        "you are now",
        "new instructions:",
    ]
    lowered = text.lower()
    for pattern in injection_patterns:
        if pattern in lowered:
            raise ValueError(f"Potential prompt injection detected: '{pattern}'")
    return text


def build_rca_chain(retriever, llm):
    """
    LCEL chain: incident → sanitize → retrieve → LLM (structured output) → RCAReport.
    Falls back to FallbackReport when retriever returns 0 results.
    """
    rca_prompt = get_rca_prompt()
    fallback_prompt = get_fallback_prompt()

    rca_llm = llm.with_structured_output(RCAReport)
    fallback_llm = llm.with_structured_output(FallbackReport)

    def run(incident_text: str):
        sanitized = _sanitize_incident(incident_text)
        docs = retriever.invoke(sanitized)

        if not docs:
            chain = fallback_prompt | fallback_llm
            return chain.invoke({"incident": sanitized})

        context = _format_docs(docs)
        chain = rca_prompt | rca_llm
        return chain.invoke({"incident": sanitized, "context": context})

    return RunnableLambda(run)


def get_llm():
    """
    Primary: Gemini free tier (requires GOOGLE_API_KEY).
    Fallback: Ollama local (USE_OLLAMA=true, must have Ollama running).
    """
    use_ollama = os.environ.get("USE_OLLAMA", "false").lower() == "true"
    if use_ollama:
        return ChatOllama(
            model="mistral:latest",
            temperature=0,
            base_url="http://localhost:11434",
            format="json",
        )
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
    )
