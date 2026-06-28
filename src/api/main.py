import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.ingestion.embedder import get_embeddings
from src.ingestion.indexer import load_vector_store
from src.retrieval.retriever import build_retriever
from src.chain.rca_chain import build_rca_chain, get_llm, _sanitize_incident

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _chain
    embeddings = get_embeddings()
    vector_store = load_vector_store(embeddings)
    llm = get_llm()
    retriever = build_retriever(vector_store, llm, use_compression=False)
    _chain = build_rca_chain(retriever, llm)
    yield


app = FastAPI(
    title="LLM RCA Agent",
    description="AI-powered Root Cause Analysis for production incidents",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


class IncidentRequest(BaseModel):
    incident: str

    model_config = {"json_schema_extra": {"example": {
        "incident": "Service auth-api returned 503 for 8 minutes starting 14:32 UTC. Error logs show connection pool exhausted."
    }}}


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}


@app.post("/analyze")
@limiter.limit("10/minute")
def analyze(request: Request, body: IncidentRequest):
    if not body.incident or not body.incident.strip():
        raise HTTPException(status_code=422, detail="Incident text cannot be empty.")
    if len(body.incident) > 8000:
        raise HTTPException(status_code=422, detail="Incident text exceeds 8000 character limit.")
    try:
        _sanitize_incident(body.incident)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        result = _chain.invoke(body.incident)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
