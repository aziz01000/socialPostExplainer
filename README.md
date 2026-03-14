# Contextual Post Explainer

AI agent that explains social media posts by searching for relevant context and returning **3–5 bullet** explanations with **citations** (e.g. [S1], [S2]). Try X’s “Explain this post” to calibrate.

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for setup instructions.

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

- **Input:** A post (text; optional image URL).
- **Flow:** Moderation → optional image analysis → retrieve context (vector DB + web + optional social/news) → LLM generation → 3–5 bullets with citations → output moderation.
- **Output:** 3–5 bullets, sources list, optional image analysis, `context_sources_used` and `context_note` (vector DB / web / external).
- **API:** `POST /explain` with `post_content` and optional `image_url`.

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
- **Multi-provider:** LLM and embeddings support OpenAI and Gemini via `LLM_PROVIDER` / `OPENAI_API_KEY` or `GEMINI_API_KEY`.
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
- [docs/architecture.md](docs/architecture.md) - System design

## License

See repository.
nothing