FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    gfortran \
    build-essential \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "if [ ! -f /app/data/faiss.index ]; then echo 'FAISS index not found. Populating vector DB...'; python scripts/populate_vector_db.py || echo 'Vector DB population failed; continuing with text-search fallback.'; fi; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
