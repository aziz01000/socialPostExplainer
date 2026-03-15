# Contextual Post Explainer

AI agent that explains social media posts by searching for relevant context and returning **3–5 bullet** explanations with **citations** (e.g. [S1], [S2]). Try X’s “Explain this post” to calibrate.

## Clone First

```bash
git clone https://github.com/aziz01000/socialPostExplainer.git
cd socialPostExplainer
```

## Fastest Start (Docker, 2 mins)

Do **not** create `.env` from scratch. Copy the template and fill only required values:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set only what is required:

```env
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

Then run:

```bash
docker compose up --build
```

Open:
- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- Phoenix Tracing (optional): `http://localhost:6006`

## Exercise requirements (spec alignment)

| Requirement | Status |
|-------------|--------|
| **AI agent** that explains social media posts by searching for and synthesizing relevant context | ✓ Agent in `backend/`; flow: retrieve (vector DB + web + optional social/news) → LLM → 3–5 bullets with citations |
| **Social/public sources** (X, Reddit, news, blogs); no Bluesky assumption | ✓ Reddit, Twitter/X, NewsData, NewsAPI, Guardian, Wikipedia-style web; all optional |
| **OpenAI API key** provided | ✓ `OPENAI_API_KEY` in `.env`; `LLM_PROVIDER=openai` to use it |
| **Frontend: React** | ✓ `frontend/` is Create React App |
| **Backend: FastAPI** | ✓ `backend/app/main.py` is FastAPI |
| **Optional ML module** (embeddings, reranking, classification, or evaluation) | ✓ Embeddings for vector search; embedding-based reranking + relevance threshold; eval harness |
| **One GitHub repo** with agent + eval harness + README | ✓ This repo |
| **Evaluation harness:** ≥10 test posts, expected outputs | ✓ `evaluation/test_posts.json` (11 posts, `expected_contains`); `run_eval.py` checks 3–5 bullets, [S#] citations, expected facts |
| **README:** setup instructions and key design decisions | ✓ Quick Start → QUICKSTART.md; Design Decisions section below |
| **Bonus: Image understanding** | ✓ Optional `image_url` on `POST /explain`; vision analysis when provided |
| **Bonus: Multi-LLM comparison** | ✓ OpenAI and Gemini via `LLM_PROVIDER` and API keys |
| **Bonus: Source citations** | ✓ [S1], [S2] in bullets; sources list; hover-to-highlight in UI |

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for full setup options (Docker + local dev).

## Project Structure

```
contextual-post-explainer/
├── backend/              # FastAPI backend, agent, retrieval
├── frontend/             # React frontend
├── evaluation/           # Eval harness (10+ test posts, expected outputs)
├── docs/                 # Documentation
└── docker-compose.yml    # Docker orchestration
```

## Agent

- **Input:** `question` text, optional image URL or uploaded image, and `sources_type` filter (`all|social|news`).
- **Flow:** Input moderation → optional image analysis → retrieval (vector DB + web + optional external APIs) → rerank/dedupe → LLM generation (3–5 bullets with [S#] citations) → output moderation.
- **Output:** Explanation bullets, sources, optional image analysis, `context_sources_used`, and `context_note`.
- **Primary API:** `POST /ask` (JSON) and `POST /ask/upload` (multipart image upload).

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Client Request                             │
│   POST /ask (question, image_url|image_base64, sources_type)        │
│   or POST /ask/upload (multipart image file)                         │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
                   ┌──────────────────────────────┐
                   │ FastAPI Route Layer          │
                   │ - validate inputs            │
                   │ - normalize uploaded image   │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │ Input Guardrail              │
                   │ (keyword + OpenAI moderation)│
                   └──────────────┬───────────────┘
                                  │
                      ╔═══════════╩═══════════╗
                      ▼                       ▼
                 ✓ PASS                    ✗ BLOCK
                 continue                  HTTP 400
                      │
                      ▼
          ┌────────────────────────────────────────────┐
          │ LangGraph Explain Workflow                 │
          │ 1) maybe_image: vision analyze (optional)  │
          │ 2) retrieve: vector_db + web + external    │
          │ 3) rerank: embeddings + relevance filter    │
          │ 4) generate: 3-5 bullets with [S#]         │
          │ 5) post_process: enforce citation format    │
          └──────────────────────┬──────────────────────┘
                                 │
                                 ▼
                   ┌──────────────────────────────┐
                   │ Output Guardrail             │
                   │ (moderation check)           │
                   └──────────────┬───────────────┘
                                  │
                      ╔═══════════╩═══════════╗
                      ▼                       ▼
                 ✓ PASS                    ✗ BLOCK
                 HTTP 200                  HTTP 400
```

## LLM Provider Choice (OpenAI vs Gemini)

You can switch providers without changing code by editing `backend/.env`:

```env
# Chat/completions provider
LLM_PROVIDER=openai        # or gemini

# Embeddings provider (can be different)
EMBEDDING_PROVIDER=openai  # or gemini
```

- **OpenAI mode:** set `OPENAI_API_KEY`.
- **Gemini mode:** set `GEMINI_API_KEY`.
- **Mixed mode supported:** for example `LLM_PROVIDER=openai` with `EMBEDDING_PROVIDER=gemini`.

## Evaluation Harness

- **Location:** `evaluation/` — `test_posts.json` (11 test posts with `expected_contains`) and `run_eval.py`.
- **Run:** From repo root, with backend deps and API key set:  
  `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` then  
  `python evaluation/run_eval.py` (evaluates the agent in-process).
- **Checks:** 3–5 bullets per response, at least one [S#] citation, and that expected key facts appear in the explanation.

## Design Decisions

- **Retrieval:** FAISS vector store (local docs) + Wikipedia (web) + optional Reddit/News/social APIs. Rerank with embeddings; dedupe by (title, url).
- **Citations:** Model is instructed to cite sources as [S1], [S2]; post-processing ensures every bullet has a citation when sources exist.
- **Guardrails:** Input and output moderation (keyword + provider) to block policy-violating content.
- **Multi-provider:** LLM and embeddings support OpenAI and Gemini via `LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `OPENAI_API_KEY`, and `GEMINI_API_KEY`.
- **Orchestration:** LangGraph workflow (moderation → optional image → retrieve → generate → post-process → output moderation) for clear steps and future branching.
- **Observability:** Arize Phoenix for tracing every LLM call; root span per request so traces stay organized.

## Observability (Arize Phoenix)

LLM calls are traced to [Arize Phoenix](https://docs.arize.com/phoenix/) when `PHOENIX_ENABLED=true`. **Run the Phoenix server via Docker** (do not `pip install arize-phoenix` in the same env as the app—it can conflict with Pydantic v2):

```bash
make phoenix
```

Then open **http://localhost:6006** to view traces. Ensure `PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006` (or leave unset for default) in `backend/.env`.

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment


## License

See repository.