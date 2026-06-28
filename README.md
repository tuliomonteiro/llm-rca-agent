# LLM RCA Agent

AI-powered Root Cause Analysis for production incidents using RAG (Retrieval-Augmented Generation).

Given an incident description, the agent retrieves semantically similar past incidents and runbook sections, then generates a structured JSON report with root cause, timeline, immediate actions, and prevention recommendations.

## Architecture

```
Incident Text
      │
      ▼
Input Validator ──── (blocks prompt injection, enforces length limit)
      │
      ▼
Sentence Transformer Embeddings  (local, free — all-MiniLM-L6-v2)
      │
      ▼
Chroma Vector Store ◄──── Runbooks + Past Incidents
      │  MMR Retrieval (k=4)
      ▼
Gemini 2.0 Flash / Mistral 7B (Ollama)
      │  with_structured_output
      ▼
RCAReport (Pydantic JSON)
```

**Fallback**: if the vector store returns 0 results, the chain returns a `FallbackReport` with `LOW` confidence and a recommendation to add relevant runbooks.

## Requirements

- Python 3.9+
- Docker (for Ollama local mode)
- One of:
  - **Google AI Studio key** — free at aistudio.google.com (key starts with `AIza`)
  - **Ollama + Mistral 7B** — fully local, no account needed

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

| Variable | Description |
|---|---|
| `GOOGLE_API_KEY` | From aistudio.google.com (free) |
| `USE_OLLAMA` | `true` to use local Mistral instead of Gemini |
| `LANGCHAIN_TRACING_V2` | `true` + `LANGSMITH_API_KEY` to enable LangSmith traces |

### 3. Start Ollama (local mode only)

```bash
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec ollama ollama pull mistral
```

Set `USE_OLLAMA=true` in `.env`.

### 4. Ingest the knowledge base

```bash
python scripts/ingest.py
```

Indexes all `.md` and `.txt` files under `data/runbooks/` and `data/incidents/` into the local Chroma vector store. Re-run whenever you add new documents.

### 5. Run a quick example

```bash
python scripts/run_example.py
```

Expected output:
```json
{
  "root_cause": "...",
  "contributing_factors": ["..."],
  "impact": "...",
  "timeline": "...",
  "immediate_actions": ["..."],
  "prevention": ["..."],
  "confidence": "HIGH"
}
```

### 6. Start the API server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs: **http://localhost:8000/docs**

### 7. Call the API

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "incident": "2024-03-15 11:30 UTC - Deployed auth-api v3.1.0. Error rate jumped to 45% at 11:45. Logs: FATAL connection pool exhausted (pool_size=10). All /login endpoints returning 503."
  }'
```

### 8. Run tests

```bash
pip install pytest
pytest tests/ -v
```

## Project Structure

```
llm-rca-agent/
├── src/
│   ├── ingestion/       # Document loading, chunking, embedding
│   ├── retrieval/       # MMR retriever + optional contextual compression
│   ├── chain/           # LCEL chain, prompts, LLM config
│   ├── parser/          # Pydantic output schemas (RCAReport, FallbackReport)
│   └── api/             # FastAPI app (/health, /analyze)
├── data/
│   ├── runbooks/        # Add your runbook .md files here
│   └── incidents/       # Add past incident reports here
├── scripts/
│   ├── ingest.py        # Build / rebuild the vector store
│   ├── run_example.py   # Quick CLI test
│   └── generate_tdd.py  # Regenerate the TDD PDF
├── tests/               # Unit tests
├── docs/                # TDD_LLM_RCA_Agent.pdf
├── .env.example
└── requirements.txt
```

## Key Design Decisions

| Decision | Why |
|---|---|
| Local embeddings (MiniLM) | Zero cost, no API key, runs on CPU. Accurate enough for incident similarity. |
| MMR retrieval | Returns diverse results — avoids 4 near-duplicate chunks from the same doc. |
| `with_structured_output` | Schema-enforced JSON — more reliable than parsing free-form text, especially on smaller models. |
| Ollama fallback | Full offline capability with Mistral 7B; flip `USE_OLLAMA=true`, no code changes needed. |
| Prompt injection guard | Incident text arrives from external systems and must be treated as untrusted input. |
| Contextual Compression | Available as opt-in (`use_compression=True`) — strips noise before the LLM sees it, saves ~40% tokens. Disabled by default to conserve free-tier quota. |

## Edge Cases Handled

| Case | Response |
|---|---|
| Empty incident text | `422 Incident text cannot be empty` |
| Input > 8,000 chars | `422 Incident text exceeds 8000 character limit` |
| Prompt injection attempt | `400 Potential prompt injection detected` |
| No matching docs in vector store | `FallbackReport` with LOW confidence + knowledge base recommendation |

## Adding Knowledge

Drop `.md` or `.txt` files into `data/runbooks/` or `data/incidents/` and re-run:

```bash
python scripts/ingest.py
```

## Switching LLM Providers

No code changes needed — controlled entirely via `.env`:

```bash
# Local Mistral via Ollama (free, private, no quota)
USE_OLLAMA=true

# Gemini 2.0 Flash via Google AI Studio (free tier)
USE_OLLAMA=false
GOOGLE_API_KEY=AIza...
```

## Production Readiness Checklist

- [ ] Enable LangSmith tracing (`LANGCHAIN_TRACING_V2=true` + `LANGSMITH_API_KEY`)
- [ ] Add API key auth header to `/analyze`
- [ ] Enable rate limiting (10 req/min per IP)
- [ ] Migrate Chroma → Qdrant Cloud for concurrent writes
- [ ] Set Google/Anthropic spend alert in provider dashboard
- [ ] Add p95 < 10s SLO alert on `/analyze`
