# FAISS Vector Database Guide

## What is FAISS?

**FAISS** (Facebook AI Similarity Search) is a library for efficient similarity search and clustering of dense vectors. It's optimized for searching through millions of vectors quickly.

## How FAISS Works

### Basic Concept

1. **Vectors** — Each document is converted to a numerical vector (embedding)
   - Text → Embedding (1536-dim for text-embedding-3-small)
   - Similar text → Similar vectors

2. **Index** — FAISS creates an index structure for fast searching
   - `IndexFlatL2` — Exact search using L2 distance (Euclidean)
   - Other options: IVF, HNSW, etc.

3. **Search** — Query vector → Find nearest neighbors
   - Returns top-k most similar documents

### Distance Metrics

- **L2 (Euclidean)** — Distance between points in space
  - Lower = more similar
  - Formula: √(Σ(a-b)²)

## Creating a FAISS Vector Database

### Step 1: Generate Embeddings

```python
from app.llm.model_router import ModelRouter

model_router = ModelRouter()
texts = ["Document 1", "Document 2", "Document 3"]
embeddings = await model_router.generate_embeddings(texts)
# Result: List of 1536-dim vectors
```

### Step 2: Create Index

```python
import faiss
import numpy as np

# Create index for 1536-dimensional vectors
index = faiss.IndexFlatL2(1536)

# Convert embeddings to float32
embeddings_array = np.array(embeddings).astype('float32')

# Add to index
index.add(embeddings_array)
```

### Step 3: Search

```python
# Query embedding
query_embedding = await model_router.generate_embeddings(["What is RAG?"])
query_array = np.array(query_embedding).astype('float32')

# Search top-5
distances, indices = index.search(query_array, k=5)

# indices[0] = [0, 2, 1, 3, 4]  (document indices)
# distances[0] = [1.5, 2.1, 2.3, 2.8, 3.1]  (L2 distances)
```

### Step 4: Save Index

```python
import faiss

# Save index
faiss.write_index(index, "path/to/faiss.index")

# Load index
index = faiss.read_index("path/to/faiss.index")
```

## Usage in Your Project

### Method 1: Automatic (Running Backend)

The vector store loads documents automatically:

```python
# In app/retrieval/vector_store.py
vector_store = VectorStore()
await vector_store.initialize()  # Loads from data/documents.json

# Search
results = await vector_store.search("Tell me about RAG", k=5)
# Returns: [(doc, relevance_score), ...]
```

### Method 2: Manual Population Script

Populate the FAISS index with embeddings:

```bash
cd backend

# With OpenAI API key configured
export OPENAI_API_KEY=sk-...
python3 scripts/populate_vector_db.py

# With Gemini API key configured
export GEMINI_API_KEY=...
export LLM_PROVIDER=gemini
python3 scripts/populate_vector_db.py

# Test the index
python3 scripts/populate_vector_db.py --test --query "What is FAISS?"
```

**Output:**
```
✓ Loaded 5 documents
✓ Generated 5 embeddings
✓ Added 5 vectors to FAISS index
✓ Saved FAISS index to: backend/data/faiss.index

📊 Statistics:
   embedding_dim: 1536
   num_vectors: 5
   num_documents: 5
   index_type: IndexFlatL2
```

## File Structure

```
backend/data/
├── documents.json           # Documents with content
├── faiss.index             # FAISS index (binary)
└── metadata.json           # Index metadata
```

**documents.json:**
```json
{
  "documents": [
    {
      "id": 1,
      "title": "Title",
      "content": "Document content...",
      "url": "https://..."
    }
  ]
}
```

**metadata.json:**
```json
{
  "embedding_dim": 1536,
  "num_vectors": 5,
  "num_documents": 5,
  "index_type": "IndexFlatL2",
  "provider": "openai",
  "model": "text-embedding-3-small"
}
```

## Advanced: Custom Index Types

### Faster Search for Large Datasets

```python
import faiss

# IVF (Inverted File Index) - good for 1M+ vectors
quantizer = faiss.IndexFlatL2(1536)
index = faiss.IndexIVFFlat(quantizer, 1536, nlist=100)
index.train(embeddings)  # Need training data
index.add(embeddings)
```

### GPU Acceleration

```python
import faiss

# Use GPU (if available)
index = faiss.IndexFlatL2(1536)
index.add(embeddings)
gpu_index = faiss.index_cpu_to_all_gpus(index)
```

## Fallback: Text-Based Search

If embeddings fail, the system falls back to keyword matching:

```python
# Automatic text search when embedding fails
results = vector_store._text_search("query", k=5)

# Score based on keyword overlap:
# - Title match: 0.8 weight
# - Content match: 0.2 weight
```

## Common Issues & Solutions

### Issue: Embedding Dimension Mismatch
```
❌ Embedding dimension mismatch: 768 vs 1536
```
**Solution:** Make sure you use consistent embedding model

### Issue: API Authentication Fails
```
❌ Embedding error: Client error '401 Unauthorized'
```
**Solution:** Check your API key in `.env`

### Issue: Out of Memory
```
❌ Memory error when loading index
```
**Solution:** Use quantization or hierarchical clustering

## Performance Tips

1. **Batch Embeddings** — Generate multiple at once (faster)
2. **Cache Results** — Save frequently accessed searches
3. **Use GPU Index** — 10-100x faster for large datasets
4. **Prune Documents** — Remove low-relevance documents periodically
5. **Monitor Index Size** — 1536-dim × 1M vectors ≈ 6GB memory

## Next Steps

- ✓ Create FAISS index with `populate_vector_db.py`
- ✓ Add custom documents to `documents.json`
- ✓ Switch between OpenAI/Gemini embeddings
- ✓ Deploy with Docker
