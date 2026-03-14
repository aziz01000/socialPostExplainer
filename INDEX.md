# Project Index

## 🚀 Start Here

**New to this project?** Read in this order:

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. **[README.md](README.md)** - Full feature overview
3. **[docs/architecture.md](docs/architecture.md)** - Understand the system
4. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - See what was built

---

## 📚 Documentation Index

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [README.md](README.md) | Complete guide with examples | 15 min |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide | 5 min |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment | 20 min |
| [docs/architecture.md](docs/architecture.md) | System architecture | 20 min |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Build overview | 10 min |
| [BUILD_CHECKLIST.md](BUILD_CHECKLIST.md) | What was built | 5 min |

---

## 🗂️ Backend Structure

### Configuration & Setup
- `backend/app/main.py` - FastAPI application (60 lines)
- `backend/app/config.py` - Settings management (40 lines)
- `backend/requirements.txt` - Python dependencies
- `backend/.env.example` - Configuration template
- `backend/Dockerfile` - Container image
- `backend/app/__init__.py` - Package init

### API Layer
```
backend/app/api/
├── routes.py         - POST /explain, GET /health endpoints
└── __init__.py
```

### Core Agent Pipeline
```
backend/app/agents/
├── post_explainer_agent.py  - 6-step LangGraph-style orchestration
│   ├── Input Guardrail
│   ├── Retrieval
│   ├── Image Analysis
│   ├── Reranking
│   ├── LLM Generation
│   └── Output Guardrail
└── __init__.py
```

### Retrieval System
```
backend/app/retrieval/
├── vector_store.py   - FAISS + OpenAI embeddings
├── web_search.py     - Web search (simulated, swappable)
└── __init__.py
```

### LLM Integration
```
backend/app/llm/
├── openai_provider.py  - OpenAI async client
├── model_router.py     - Multi-provider router
└── __init__.py
```

### Safety & Guardrails
```
backend/app/guardrails/
├── moderation.py     - OpenAI moderation API
└── __init__.py
```

### Observability
```
backend/app/observability/
├── phoenix_tracing.py - Custom Phoenix tracer
└── __init__.py
```

### Data Models
```
backend/app/models/
├── schemas.py  - All Pydantic models
└── __init__.py
```

---

## 🎨 Frontend Structure

### Main Application
- `frontend/src/App.js` - Main component (90 lines)
- `frontend/src/App.css` - Main styles
- `frontend/src/api.js` - Backend API client
- `frontend/src/index.js` - React entry point

### Components
```
frontend/src/components/
├── PostInput.js        - Input form (60 lines)
├── PostInput.css       - Input styles
├── ExplanationView.js  - Display results (40 lines)
├── ExplanationView.css - Display styles
├── SourceList.js       - Citations (50 lines)
└── SourceList.css      - Citation styles
```

### Configuration
- `frontend/public/index.html` - HTML template
- `frontend/package.json` - Dependencies
- `frontend/Dockerfile` - Multi-stage build
- `frontend/nginx.conf` - Nginx config

---

## 🧪 Evaluation & Testing

```
evaluation/
├── evaluator.py       - Test harness (200 lines)
├── test_posts.json    - 10 test posts
└── results.json       - Generated results
```

### Test Posts Coverage
1. Latest AI models launch
2. Deep learning & transformers
3. RAG systems
4. Vector embeddings
5. FAISS library
6. LLMs & few-shot learning
7. Guardrails for safety
8. Observability & monitoring
9. Content moderation
10. Production best practices

---

## 🚀 Quick Commands Reference

```bash
# Setup & Installation
bash setup.sh              # Initial setup
make install              # Install dependencies

# Development
make run                  # Start everything
make run-backend          # Backend only (port 8000)
make run-frontend         # Frontend only (port 3000)

# Testing & Evaluation
make evaluate             # Run evaluation harness
make test                 # Same as evaluate

# Docker
make docker-build         # Build images
make docker-up            # Start with docker-compose
make docker-down          # Stop docker-compose

# Maintenance
make clean               # Remove cache
make clean-all           # Remove everything

# Manual startup (if needed)
bash run.sh              # Start services
bash evaluate.sh         # Run evaluation
```

---

## 🔑 Configuration Reference

### Essential Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...               # Your OpenAI key

# LLM Configuration
LLM_PROVIDER=openai                 # openai or anthropic
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Retrieval
TOP_K_DOCUMENTS=5
RERANK_TOP_K=3

# Safety
ENABLE_INPUT_MODERATION=true
ENABLE_OUTPUT_MODERATION=true

# Observability
PHOENIX_ENABLED=true
PHOENIX_PROJECT_NAME=contextual-post-explainer
```

See `backend/.env.example` for all options.

---

## 🏗️ Architecture Overview

```
                    Browser
                       ↓
                    React App
                    (3000)
                       ↓
    ┌──────────────── API ────────────────┐
    │                                     │
    │    FastAPI Backend (8000)          │
    │                                     │
    │  POST /explain Endpoint             │
    │    ↓                                │
    │  Agent Pipeline (6 steps)          │
    │    ├─ Input Safety Check           │
    │    ├─ Hybrid Retrieval             │
    │    ├─ Image Analysis               │
    │    ├─ Reranking                    │
    │    ├─ LLM Generation               │
    │    └─ Output Safety Check          │
    │    ↓                                │
    │  Response w/ Explanation & Sources │
    │                                     │
    └─────────────────────────────────────┘
            ↓           ↓           ↓
         FAISS      OpenAI       Moderation
        (Vector)     (LLM)         (API)
```

---

## 📈 Metrics & Performance

**Realistic Expectations:**
- Response time: 2-3 seconds
- Keyword coverage: 70-85%
- Vector search: 50-100ms
- LLM generation: 1-2 seconds
- Token usage: 300-500 per request

See [docs/architecture.md](docs/architecture.md#performance-characteristics) for details.

---

## 🔐 Security Checklist

- ✅ Input moderation with OpenAI
- ✅ Output moderation with OpenAI
- ✅ API key in environment (not hardcoded)
- ✅ Type validation on all inputs
- ✅ CORS configured for frontend
- ✅ Error handling without stack traces

For production, also see [DEPLOYMENT.md#security-hardening](DEPLOYMENT.md#security-hardening).

---

## 🚢 Deployment Options

1. **Local Development** - See [QUICKSTART.md](QUICKSTART.md)
2. **Docker Compose** - `make docker-up`
3. **Kubernetes** - See [DEPLOYMENT.md](DEPLOYMENT.md#option-2-kubernetes)
4. **Cloud** - AWS/GCP/Heroku - See [DEPLOYMENT.md](DEPLOYMENT.md#option-3-cloud-platforms)

---

## 🧠 Understanding the Code

### Start with These Files
1. `backend/app/main.py` - FastAPI setup
2. `backend/app/agents/post_explainer_agent.py` - Agent workflow
3. `frontend/src/App.js` - React main app
4. `evaluation/evaluator.py` - Test runner

### Key Concepts
- **Async/Await**: All I/O is non-blocking
- **Pydantic**: Request/response validation
- **FAISS**: Vector similarity search
- **LangGraph-style**: Sequential pipeline execution
- **Phoenix**: Observability tracing

---

## 🐛 Troubleshooting Quick Links

| Issue | Solution |
|-------|----------|
| API key error | Check `backend/.env` has `OPENAI_API_KEY` |
| Backend won't start | Run `python -m app.main`, check port 8000 |
| Frontend can't connect | Ensure backend running, check logs |
| Docker build fails | Clear `docker system prune`, rebuild |
| FAISS error | Install with `pip install faiss-cpu` |
| Port already in use | Change ports in docker-compose.yml |

See [QUICKSTART.md#troubleshooting](QUICKSTART.md#troubleshooting) for more.

---

## 📞 Support Resources

- **API Documentation**: [README.md#api-usage](README.md#api-usage)
- **Architecture Details**: [docs/architecture.md](docs/architecture.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Code Examples**: In component files with docstrings

---

## 🎓 Learning Path

**Beginner**:
1. QUICKSTART.md - Get it running
2. README.md - Understand features
3. Try the UI at `http://localhost:3000`

**Intermediate**:
1. docs/architecture.md - See the design
2. Review `backend/app/agents/post_explainer_agent.py`
3. Run evaluation, tweak test posts

**Advanced**:
1. Study all backend modules
2. Implement real web search API
3. Add Redis caching layer
4. Deploy to production

---

## ✨ Project Highlights

- ✅ **Production-ready** code quality
- ✅ **Type-safe** with Pydantic & Python hints
- ✅ **Fully async** for high concurrency
- ✅ **Observable** with Phoenix tracing
- ✅ **Safe** with input/output guardrails
- ✅ **Documented** with guides & examples
- ✅ **Tested** with evaluation harness
- ✅ **Containerized** with Docker
- ✅ **Scalable** stateless design
- ✅ **Educational** clean code patterns

---

## 🎯 Next Steps

1. **Setup**: Run `bash setup.sh`
2. **Configure**: Set `OPENAI_API_KEY` in `backend/.env`
3. **Run**: Execute `make run`
4. **Test**: Visit `http://localhost:3000`
5. **Evaluate**: Run `make evaluate`
6. **Deploy**: Use `make docker-up`

---

**Built with ❤️ using FastAPI, React, LangGraph patterns, and OpenAI**
