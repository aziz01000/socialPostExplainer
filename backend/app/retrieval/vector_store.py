"""FAISS vector store for semantic search."""

import faiss
import numpy as np
from typing import List, Tuple
from app.llm.model_router import ModelRouter


class VectorStore:
    """FAISS-based vector store."""
    
    def __init__(self):
        self.index = None
        self.documents = []
        self.model_router = ModelRouter()
        self.embedding_dim = 1536  # text-embedding-3-small dimension
    
    async def initialize(self):
        """Initialize FAISS index."""
        self.index = faiss.IndexFlatL2(self.embedding_dim)
    
    async def add_documents(self, documents: List[dict]) -> None:
        """Add documents to vector store.
        
        Each document should have 'id', 'content', 'title', 'url' fields.
        """
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
    
    async def search(self, query: str, k: int = 5) -> List[Tuple[dict, float]]:
        """Search for similar documents.
        
        Returns list of (document, score) tuples.
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Embed query
        query_embeddings = await self.model_router.generate_embeddings([query])
        query_array = np.array(query_embeddings).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_array, k)
        
        # Build results
        results = []
        for dist, idx in zip(distances[0], indices):
            if idx >= 0 and idx < len(self.documents):
                results.append((self.documents[idx], float(dist)))
        
        return results
