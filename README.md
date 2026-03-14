# Contextual Post Explainer

A production-grade AI system that explains social media posts with retrieved context and source citations. Built with **LangGraph**, **FastAPI**, **React**, and powered by **OpenAI**.

## Features

✨ **Hybrid Retrieval** - Combines vector search + web search for comprehensive context  
🔐 **Guardrails** - Input & output moderation using OpenAI API  
📊 **Observability** - Phoenix tracing for prompts, tokens, latency, and context  
🖼️ **Image Understanding** - Optional vision analysis of images with posts  
⚡ **Production-Ready** - Type hints, clean code, modular architecture  
🚀 **Containerized** - Docker & Docker Compose setup  
📈 **Evaluation** - Built-in evaluation harness with metrics  

## Architecture

```
Input Post
    ↓
[Input Guardrail] → Check if safe
    ↓
[Retrieval Layer] → Vector + Web Search
    ↓
[Rerank Context] → Sort by relevance
    ↓
[Image Analysis] → (Optional) Analyze image
    ↓
[LLM Explanation] → Generate with context
    ↓
[Output Guardrail] → Check output safety
    ↓
[Return] → Explanation + Sources
```

## Tech Stack

### Backend
- **Framework**: FastAPI with async/await
- **Agent**: LangGraph-style workflow
- **Retrieval**: FAISS (vector) + simulated web search
- **LLM**: OpenAI GPT-4o-mini + embeddings
- **Guardrails**: OpenAI moderation API
- **Observability**: Custom Phoenix tracer
- **Async HTTP**: httpx

### Frontend
- **Framework**: React 18
- **State**: React hooks
- **HTTP Client**: Axios
- **Styling**: CSS3 with design system

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)
- OpenAI API key

### Setup

1. **Clone & navigate**
```bash
cd contextual-post-explainer
```

2. **Configure environment**
```bash
cd backend
cp .env.example .env
# Edit .env and add your OpenAI API key
export OPENAI_API_KEY=sk-...
```

3. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

4. **Run backend (development)**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Install & run frontend**
```bash
cd frontend
npm install
REACT_APP_API_BASE_URL=http://localhost:8000 npm start
```

Frontend will be available at `http://localhost:3000`

## API Usage

### Explain Endpoint

**Request:**
```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "post": "Just launched our new AI model with SOTA benchmarks! #AI #ML",
    "image_url": "https://example.com/image.jpg"
  }'
```

**Response:**
```json
{
  "explanation": "• Large Language Models (LLMs) are pre-trained neural networks...\n• State-of-the-art (SOTA) refers to the best performance...",
  "sources": [
    {
      "url": "https://example.com/ai-basics",
      "title": "AI Basics",
      "context": "Artificial Intelligence... [truncated for brevity]"
    }
  ],
  "image_analysis": "The image shows a chart with performance metrics..."
}
```

## Evaluation

Run the evaluation harness on 10 test posts:

```bash
cd backend
python -m evaluation.evaluator
```

**Output:**
```
==================================================
EVALUATION RESULTS
==================================================
Total Posts: 10
Successful: 10
Failed: 0
Avg Keyword Coverage: 78.50%
Avg Response Time: 2345.67ms
==================================================
```

Results are saved to `evaluation/results.json`

## Docker Deployment

### Build & run with Docker Compose
```bash
docker-compose up --build
```

This will:
- Build backend image (FastAPI)
- Build frontend image (React + Nginx)
- Start Phoenix tracing service
- Expose backend on `http://localhost:8000`
- Expose frontend on `http://localhost:3000`
- Expose Phoenix on `http://localhost:6006`

### Environment variables
Create a `.env` file in the root directory:
```
OPENAI_API_KEY=sk-...
```

## Project Structure

```
contextual-post-explainer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── api/
│   │   │   └── routes.py        # API endpoints
│   │   ├── agents/
│   │   │   └── post_explainer_agent.py  # LangGraph agent
│   │   ├── retrieval/
│   │   │   ├── vector_store.py  # FAISS
│   │   │   └── web_search.py    # Web retrieval
│   │   ├── llm/
│   │   │   ├── openai_provider.py
│   │   │   └── model_router.py  # Multi-provider support
│   │   ├── guardrails/
│   │   │   └── moderation.py    # Input/output safety
│   │   ├── observability/
│   │   │   └── phoenix_tracing.py
│   │   └── models/
│   │       └── schemas.py       # Pydantic models
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.js
│   │   ├── app.css
│   │   ├── api.js               # Backend client
│   │   ├── components/
│   │   │   ├── PostInput.js
│   │   │   ├── ExplanationView.js
│   │   │   └── SourceList.js
│   │   └── index.js
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── evaluation/
│   ├── test_posts.json          # 10 test posts
│   ├── evaluator.py             # Evaluation harness
│   └── results.json             # Results output
├── docs/
│   └── architecture.md          # Architecture diagram
└── docker-compose.yml
```

## Configuration

### Backend Settings (`backend/app/config.py`)

```python
# LLM Provider (openai, anthropic)
LLM_PROVIDER = "openai"

# Vector search top-k
TOP_K_DOCUMENTS = 5
RERANK_TOP_K = 3

# Guardrails
ENABLE_INPUT_MODERATION = True
ENABLE_OUTPUT_MODERATION = True

# Phoenix tracing
PHOENIX_ENABLED = True
```

## Advanced Features

### 1. Image Understanding
If `image_url` is provided, the system:
- Sends image + post to GPT-4o vision
- Includes visual analysis in explanation
- Cites visual context in sources

### 2. Multi-Provider LLM Router
Support for multiple LLM providers:
```python
# Switch provider via environment
LLM_PROVIDER=openai  # or anthropic
```

### 3. Guardrails
- **Input moderation**: Detects unsafe post content
- **Output moderation**: Prevents problematic explanations
- **Fail-open**: Returns safe default on API errors

### 4. Phoenix Observability
Tracks:
- LLM calls (prompts, responses, tokens)
- Retrieval operations (query, results, latency)
- Agent workflow steps
- Moderation checks
- Total latency & costs

Exported to `traces.json` on shutdown.

## Performance Metrics

- **Latency**: ~2-3 seconds per post (varies with API delays)
- **Tokens**: ~300-500 tokens per request
- **Retrieval**: ~100-300ms for vector + web search
- **Moderation**: ~200-400ms for input/output checks

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Verify OpenAI API key in `.env`
- Check port 8000 is available

### Frontend can't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in `app/main.py`
- Verify `REACT_APP_API_BASE_URL` environment variable

### FAISS index creation fails
- Install FAISS: `pip install faiss-cpu`
- Ensure `data/` directory exists
- Check disk space for embeddings cache

## Testing

### Evaluate on test posts
```bash
cd backend
python -m evaluation.evaluator
```

### Manual API test
```bash
curl -X GET http://localhost:8000/health
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{"post": "Test post"}'
```

## Future Enhancements

- [ ] Support for more LLM providers (Claude, Gemini)
- [ ] Real web search integration (SerpAPI, Bing)
- [ ] Streaming responses for faster UI updates
- [ ] Fine-tuned ranking models for context selection
- [ ] Multi-language support
- [ ] Advanced caching strategies
- [ ] Analytics dashboard
- [ ] User feedback loop for model improvement

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## Support

For issues and questions:
- Check documentation in `docs/`
- Review test posts in `evaluation/test_posts.json`
- Enable debug mode: `DEBUG=true` in `.env`
