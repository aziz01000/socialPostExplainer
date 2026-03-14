# Architecture

## System Overview

The Contextual Post Explainer is a modular, production-grade AI system that explains social media posts with retrieved context and verifiable sources.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
├─────────────────────────────────────────────────────────────┤
│  PostInput → ExplanationView → SourceList                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│                  POST /explain                              │
│  ExplainRequest → ExplainResponse                           │
└──────────┬──────────────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────────────────────────┐
│          Post Explainer Agent (LangGraph Style)             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────┐              │
│  │ Input Guardrail │ → │ Check Safety API │              │
│  └─────────────────┘    └──────────────────┘              │
│           │                                                │
│           ↓                                                │
│  ┌──────────────────────────────────────────┐             │
│  │    Retrieval Layer (Hybrid)              │             │
│  │ ┌─────────────────────────────────────┐  │             │
│  │ │ Vector Search (FAISS)               │  │             │
│  │ │ + Web Search (Simulated)            │  │             │
│  │ └─────────────────────────────────────┘  │             │
│  └──────────────────────────────────────────┘             │
│           │                                                │
│           ↓                                                │
│  ┌──────────────────────┐                                 │
│  │ Rerank Documents     │                                 │
│  │ Sort by Relevance    │                                 │
│  └──────────────────────┘                                 │
│           │                                                │
│           ↓                                                │
│  ┌──────────────────────────────────────────┐             │
│  │  Image Analysis (Optional)               │             │
│  │  GPT-4o Vision on Image + Post          │             │
│  └──────────────────────────────────────────┘             │
│           │                                                │
│           ↓                                                │
│  ┌──────────────────────────────────────────┐             │
│  │  LLM Explanation Generation              │             │
│  │  GPT-4o-mini with Context + Citations   │             │
│  └──────────────────────────────────────────┘             │
│           │                                                │
│           ↓                                                │
│  ┌─────────────────┐    ┌──────────────────┐ │            │
│  │Output Guardrail │ → │ Check Safety API │ │            │
│  └─────────────────┘    └──────────────────┘ │            │
│           │                                   │            │
│           ↓                                   │            │
│  ┌─────────────────────────────────────────┐ │            │
│  │ Return Explanation + Sources            │ │            │
│  └─────────────────────────────────────────┘ │            │
└─────────────────────────────────────────────────────────────┘
           ↑
           │ Observability
           │
     ┌─────────────┐
     │ Phoenix     │
     │ Tracing     │
     └─────────────┘
```

## Component Details

### 1. Frontend (React)

**Components:**
- `PostInput`: Textarea for post + optional image URL
- `ExplanationView`: Displays bullet-point explanation
- `SourceList`: Shows clickable source citations

**Data Flow:**
```
User Input → PostInput → API Call → Receive Response → 
ExplanationView + SourceList
```

### 2. API Layer (FastAPI)

**Endpoint:** `POST /explain`

**Request:**
```json
{
  "post": "string",
  "image_url": "optional string"
}
```

**Response:**
```json
{
  "explanation": "string (bullet points)",
  "sources": [
    {
      "url": "string",
      "title": "string",
      "context": "string"
    }
  ],
  "image_analysis": "optional string"
}
```

### 3. Agent Workflow

The agent executes a sequential pipeline:

1. **Input Guardrail**: Check post safety with moderation API
2. **Retrieval**: Fetch top-3 vector results + top-2 web results
3. **Image Analysis**: Optional vision analysis if image provided
4. **Reranking**: Sort by relevance score
5. **LLM Generation**: Create explanation with OpenAI
6. **Output Guardrail**: Verify explanation safety
7. **Return**: Package results with sources

### 4. Retrieval Layer

**Hybrid Approach:**
- **Vector Search**: FAISS index with OpenAI embeddings
  - Semantic similarity search
  - Sub-100ms queries on CPU
  - Sample documents pre-embedded
  
- **Web Search**: Simulated for prototype
  - Keyword-based lookup in content DB
  - Production: Integrate SerpAPI or Bing

**Results Combination:**
- Top-3 vector results
- Top-2 web results
- Rerank combined by relevance score

### 5. LLM Provider

**OpenAI Integration:**
- **Generation**: `gpt-4o-mini` for explanations
- **Embeddings**: `text-embedding-3-small` (1536-dim)
- **Vision**: `gpt-4o` for image analysis

**Async HTTP Client:**
- Uses `httpx` for concurrent requests
- Timeout: 30 seconds per request
- Automatic retry on transient errors

### 6. Guardrails

**Moderation API:**
- Checks 14 safety categories
- Returns category flags and overall safety status

**Input Moderation:**
- Prevents unsafe content from being explained
- Graceful error response

**Output Moderation:**
- Flags potentially harmful explanations
- Replaces with safe alternative response

### 7. Observability (Phoenix)

**Tracked Metrics:**
- LLM calls: prompt length, response length, tokens, latency
- Retrieval: query, num results, latency, result summary
- Agent steps: step name, state, latency, errors
- Moderation: check type, flagged status, categories, latency

**Export:**
- JSON export to `traces.json`
- Integration point for Phoenix platform

## Data Models

### AgentState
```python
class AgentState(BaseModel):
    post: str
    image_url: Optional[str]
    moderation_input_safe: bool
    retrieval_results: list[RetrievalResult]
    reranked_results: list[RetrievalResult]
    image_analysis: Optional[str]
    explanation: str
    moderation_output_safe: bool
    sources: list[Source]
    error: Optional[str]
```

### RetrievalResult
```python
class RetrievalResult(BaseModel):
    document: str
    source: str
    relevance_score: float
    url: Optional[str]
```

## Error Handling

**Input Safety Violation:**
```
HTTP 400
{
  "detail": "Input content violates content policy"
}
```

**Processing Error:**
```
HTTP 500
{
  "detail": "Failed to process request"
}
```

**Graceful Fallbacks:**
- Missing OpenAI key: Uses environment variable
- Moderation API down: Fail-open (allows content)
- Vector search unavailable: Web search only
- Image analysis fails: Continues without image context

## Performance Characteristics

### Latency Breakdown
- Input moderation: 200-400ms
- Vector search: 50-100ms
- Web search: 50-150ms
- Reranking: <10ms
- LLM generation: 1-2 seconds
- Output moderation: 200-400ms
- **Total**: 2-3 seconds

### Token Usage
- Prompt: 200-300 tokens
- Response: 100-200 tokens
- **Total**: 300-500 tokens per request
- Cost: ~$0.0003 per request (using gpt-4o-mini)

### Scalability
- FastAPI with async/await: handles 100+ concurrent requests
- Redis caching layer: potential addition
- Horizontal scaling: stateless design

## Deployment Options

### Development
```bash
backend$ uvicorn app.main:app --reload
frontend$ npm start
```

### Production (Docker)
```bash
docker-compose up --build
```

Includes:
- Backend (FastAPI + Uvicorn)
- Frontend (React + Nginx)
- Phoenix tracing service

## Security Considerations

1. **API Key Management**
   - OpenAI key in environment variables
   - Not hardcoded or logged

2. **CORS Configuration**
   - Frontend-backend communication
   - Configurable origin whitelist

3. **Content Moderation**
   - Two-layer safety checks
   - OpenAI moderation API

4. **Input Validation**
   - Pydantic schemas for type safety
   - Length limits on inputs

## Future Architecture Enhancements

1. **Vector Store**
   - Upgrade to FAISS GPU version
   - Add Pinecone/Weaviate cloud storage

2. **Retrieval**
   - Real web search integration
   - Cached results layer

3. **LLM Providers**
   - Abstract provider interface
   - Support Anthropic, Gemini

4. **Observability**
   - Real Phoenix platform integration
   - Datadog/New Relic dashboard

5. **Caching**
   - Redis for embedding cache
   - HTTP caching headers

6. **Monitoring**
   - Prometheus metrics
   - Health check dashboard
   - Alert thresholds
