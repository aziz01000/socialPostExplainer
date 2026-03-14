"""FAISS vector store for semantic search."""

import faiss
import numpy as np
import json
import os
from typing import List, Tuple, Dict
from app.llm.model_router import ModelRouter


class VectorStore:
    """FAISS-based vector store."""
    
    def __init__(self, data_dir: str = "data"):
        self.index = None
        self.documents = []
        self.model_router = ModelRouter()
        self.embedding_dim = 1536  # text-embedding-3-small dimension
        self.data_dir = data_dir
        self.index_path = os.path.join(data_dir, "faiss.index")
        self.docs_path = os.path.join(data_dir, "documents.json")
    
    async def initialize(self):
        """Initialize FAISS index."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Try loading existing index
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.docs_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                print(f"✓ Loaded existing index with {len(self.documents)} documents")
                return
            except Exception as e:
                print(f"Failed to load existing index: {e}")
        
        # Create new index
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Try to load documents from JSON without embeddings
        if os.path.exists(self.docs_path):
            try:
                with open(self.docs_path, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                print(f"✓ Loaded {len(self.documents)} documents from file (text search mode)")
                return
            except Exception as e:
                print(f"Failed to load documents: {e}")
        
        print("✓ Created new FAISS index (empty)")
    
    async def _add_sample_documents(self):
        """Add sample documents for testing."""
        sample_docs = [
            {
                "id": 1,
                "title": "Understanding RAG Systems",
                "content": "Retrieval Augmented Generation (RAG) combines retrieval and generation. It retrieves relevant documents and uses them as context for generating responses.",
                "url": "https://example.com/rag"
            },
            {
                "id": 2,
                "title": "What is FAISS?",
                "content": "FAISS (Facebook AI Similarity Search) is a library for efficient similarity search and clustering of dense vectors. It handles large-scale similarity search.",
                "url": "https://example.com/faiss"
            },
            {
                "id": 3,
                "title": "Embeddings Explained",
                "content": "Text embeddings convert text into numerical vectors. They capture semantic meaning, allowing similar texts to have similar vector representations.",
                "url": "https://example.com/embeddings"
            },
            {
                "id": 4,
                "title": "Vector Search Basics",
                "content": "Vector search finds similar items by comparing their vector representations. It's faster than keyword search for semantic retrieval.",
                "url": "https://example.com/vector-search"
            },
            {
                "id": 5,
                "title": "LLM Context Windows",
                "content": "Large language models have context windows limiting input size. RAG helps by providing only the most relevant context.",
                "url": "https://example.com/context-windows"
            }
        ]
        
        await self.add_documents(sample_docs)
    
    async def add_documents(self, documents: List[Dict]) -> None:
        """Add documents to vector store."""
        if not documents:
            return
        
        # Extract texts
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        embeddings = await self.model_router.generate_embeddings(texts)
        
        # Add to FAISS
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        
        # Store documents
        self.documents.extend(documents)
        
        # Save to disk
        self._save_index()
        print(f"✓ Added {len(documents)} documents. Total: {len(self.documents)}")
    
    async def search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """Search for similar documents.
        
        Returns list of (document, relevance_score) tuples, ordered by relevance.
        Uses FAISS if available, falls back to text-based search.
        """
        if self.index is None or self.index.ntotal == 0:
            # Fallback: text-based search
            return self._text_search(query, k)
        
        try:
            # Embed query
            query_embeddings = await self.model_router.generate_embeddings([query])
            query_array = np.array(query_embeddings).astype('float32')
            
            # Search - FAISS returns distances (lower is better for L2)
            distances, indices = self.index.search(query_array, min(k, self.index.ntotal))
            
            # Build results with relevance scores
            results = []
            max_distance = np.max(distances[0]) if distances[0].size > 0 else 1.0
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    # Convert distance to similarity score (0-1)
                    relevance_score = 1.0 - (dist / (max_distance + 1e-6))
                    results.append((self.documents[idx], relevance_score))
            
            return results
        except Exception as e:
            print(f"Embedding search failed: {e}, falling back to text search")
            return self._text_search(query, k)
    
    def _text_search(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """Fallback text-based search using keyword matching.
        
        Simple implementation that scores documents based on keyword overlap.
        """
        query_words = set(query.lower().split())
        
        results = []
        for doc in self.documents:
            title = doc.get("title", "").lower()
            content = doc.get("content", "").lower()
            
            # Calculate score based on word overlap
            title_words = set(title.split())
            content_words = set(content.split())
            
            title_overlap = len(query_words & title_words) / (len(query_words) + 1e-6)
            content_overlap = len(query_words & content_words) / (len(query_words) + 1e-6)
            
            # Weight title matches higher
            score = (title_overlap * 0.8) + (content_overlap * 0.2)
            
            if score > 0:
                results.append((doc, score))
        
        # Sort by score and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def _save_index(self):
        """Save index and documents to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.docs_path, 'w') as f:
                json.dump(self.documents, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save index: {e}")
    
    def clear(self):
        """Clear the index."""
        self.documents = []
        self.index = faiss.IndexFlatL2(self.embedding_dim)
