# Quick Start Guide

## 🚀 Getting Started (5 minutes)

### Option 1: Local Development (Recommended)

#### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

#### 2. Setup
```bash
# Clone the repository
cd contextual-post-explainer

# Run setup script
bash setup.sh

# Configure OpenAI API key
nano backend/.env
# Set: OPENAI_API_KEY=sk-your-key-here
```

#### 3. Run Services
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
REACT_APP_API_BASE_URL=http://localhost:8000 npm start
```

Open http://localhost:3000 in your browser ✨

### Option 2: Docker (Recommended for production)

#### 1. Prerequisites
- Docker
- Docker Compose
- OpenAI API key

#### 2. Setup
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your OpenAI API key
```

#### 3. Run
```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Phoenix Tracing: http://localhost:6006 (optional)

### Option 3: Using Makefile

```bash
# Setup
make setup

# Run everything
make run

# Split terminals (if needed):
make run-backend
make run-frontend

# Evaluate on test posts
make evaluate

# Docker
make docker-up
```

## 📝 Example Usage

### Via UI (http://localhost:3000)

1. Enter a post: "Just learned about RAG systems - game changer for AI!"
2. (Optional) Add image URL
3. Click "Explain Post"
4. View explanation + source citations

### Via API

```bash
curl -X POST http://localhost:8000/explain \
  -H "Content-Type: application/json" \
  -d '{
    "post": "AI and machine learning transforming industries",
    "image_url": null
  }'
```

Response:
```json
{
  "explanation": "• AI (Artificial Intelligence) refers to simulation...",
  "sources": [
    {
      "url": "https://example.com/ai-basics",
      "title": "AI Basics",
      "context": "AI is the simulation of human intelligence..."
    }
  ],
  "image_analysis": null
}
```

## 🧪 Evaluation

Run the evaluation harness on 10 test posts:

```bash
make evaluate
```

Output:
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

## 🧹 Cleanup

```bash
# Remove cache and temp files
make clean

# Remove everything (including venv and node_modules)
make clean-all
```

## ❓ Troubleshooting

### Backend fails to start
```bash
# Check Python version
python3 --version  # Need 3.11+

# Check OpenAI API key
cat backend/.env | grep OPENAI_API_KEY

# Check port 8000 is free
lsof -i :8000
```

### Frontend can't connect
```bash
# Check backend is running
curl http://localhost:8000/health

# Check environment variable
echo $REACT_APP_API_BASE_URL
```

### FAISS index error
```bash
# Install FAISS
pip install faiss-cpu

# Clear cached index
rm -rf backend/data/*

# Restart backend
```

## 📚 Documentation

- [README.md](../README.md) - Full documentation
- [Architecture](../docs/architecture.md) - System design
- [Backend API](../backend/app/api/routes.py) - API endpoints
- [Test Posts](../evaluation/test_posts.json) - Sample test posts

## 🎯 Next Steps

1. ✅ Explore the UI with sample posts
2. ✅ Review the [architecture diagram](../docs/architecture.md)
3. ✅ Run evaluation with `make evaluate`
4. ✅ Check traces with Phoenix at http://localhost:6006 (if Docker)
5. ✅ Modify test posts in `evaluation/test_posts.json`
6. ✅ Deploy with Docker Compose

## 💡 Pro Tips

- **Debug mode**: Set `DEBUG=true` in `backend/.env`
- **Custom test posts**: Edit `evaluation/test_posts.json`
- **Real web search**: Replace simulated search in `backend/app/retrieval/web_search.py` with SerpAPI
- **GPU FAISS**: Install `faiss-gpu` for faster vector search
- **Caching**: Add Redis for embedding cache in production

Enjoy! 🚀
