# Quick Start

## Option A (Recommended): Docker Compose

### 1) Create `.env` from template

```bash
cp backend/.env.example backend/.env
```

### 2) Edit only required variables in `backend/.env`

Minimum required:

```env
OPENAI_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

Optional (if you want external social/news APIs):

```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
TWITTER_BEARER_TOKEN=
NEWSDATA_API_KEY=
NEWSAPI_API_KEY=
GUARDIAN_API_KEY=
```

### 3) Run everything

```bash
docker compose up --build
```

### 4) Access services

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend docs: `http://localhost:8000/docs`
- Phoenix traces (optional): `http://localhost:6006`

---

## Option B: Local Development (without Docker)

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

## Setup (local)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set at least one of `OPENAI_API_KEY` or `GEMINI_API_KEY`. The backend needs a FAISS index: ensure `backend/data/` contains `faiss.index` and `documents.json` (or run `python scripts/populate_vector_db.py --docs data/documents.json` to build it).

### 2. Frontend

```bash
cd frontend
npm install
```

## Development

### Start Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm start
```

Frontend runs at `http://localhost:3000`

## Run Evaluation

From the repo root, with backend dependencies installed and `OPENAI_API_KEY` or `GEMINI_API_KEY` set in `backend/.env`:

```bash
cd backend && source venv/bin/activate
python ../evaluation/run_eval.py
```

The harness runs 11 test posts in-process, checks for 3–5 bullets, [S#] citations, and expected key phrases.

## Docker

```bash
docker-compose up --build
```

All services run in containers.
