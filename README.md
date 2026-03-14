# Contextual Post Explainer

AI-powered social media post explainer with retrieval augmented generation (RAG).

## Quick Start

See [QUICKSTART.md](QUICKSTART.md) for setup instructions.

## Project Structure

```
contextual-post-explainer/
├── backend/              # FastAPI backend
├── frontend/            # React frontend
├── evaluation/          # Evaluation harness
├── docs/               # Documentation
└── docker-compose.yml  # Docker orchestration
```

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

## Status

🚧 Under development
