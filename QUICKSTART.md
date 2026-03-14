# Quick Start

## Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

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

## Docker

```bash
docker-compose up --build
```

All services run in containers.
