"""FAISS vector store for semantic search."""

import faiss
import numpy as np
import json
import os
from typing import List, Tuple, Dict, Any
from app.llm.model_router import ModelRouter
from app.config import settings


class VectorStore:
    """FAISS-based vector store."""
    
    def __init__(self, data_dir: str = None):
        self.index = None
        self.documents = []
        self.model_router = ModelRouter()
        # Default to configured embedding dimensions; metadata/index load may override.
        # OpenAI's text-embedding-3-small is 1536, Gemini embedding can be 3072, etc.
        self.embedding_dim = int(getattr(settings, "embedding_dimensions", 1536) or 1536)
        
        # Use absolute path relative to backend root, not current working directory
        if data_dir is None:
            # Get backend root directory (go up from app/retrieval/vector_store.py)
            backend_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            data_dir = os.path.join(backend_root, "data")
        
        self.data_dir = data_dir
        self.index_path = os.path.join(data_dir, "faiss.index")
        self.docs_path = os.path.join(data_dir, "documents.json")
        self.metadata_path = os.path.join(data_dir, "metadata.json")
        
        print(f"🗂️  VectorStore initialized with data_dir: {self.data_dir}")
    
    async def initialize(self):
        """Initialize FAISS index."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Try loading existing index
        if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
            try:
                print(f"📂 Found index files, attempting to load...")
                self.index = faiss.read_index(self.index_path)
                with open(self.docs_path, 'r') as f:
                    data = json.load(f)
                    # Support both legacy list format and current {"documents": [...]} format.
                    if isinstance(data, list):
                        self.documents = data
                    else:
                        self.documents = data.get("documents", [])
                
                # Load embedding dimension from metadata if available
                if os.path.exists(self.metadata_path):
                    try:
                        with open(self.metadata_path, 'r') as f:
                            metadata = json.load(f)
                            loaded_dim = metadata.get("embedding_dim", self.embedding_dim)
                            self.embedding_dim = loaded_dim
                            print(f"📊 Loaded embedding_dim from metadata: {loaded_dim}")
                    except Exception as e:
                        print(f"⚠️  Failed to load metadata: {e}")
                
                print(f"✓ Loaded existing FAISS index:")
                print(f"   Documents: {len(self.documents)}")
                print(f"   Vectors in index: {self.index.ntotal}")
                print(f"   Embedding dimension: {self.embedding_dim}")
                
                if self.index.ntotal == 0:
                    print(f"❌ WARNING: FAISS index has 0 vectors!")
                
                return
            except Exception as e:
                print(f"❌ Failed to load existing index: {e}")
                print(f"   Attempting to create new index...")
        
        # Create new index
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        
        # Try to load documents from JSON without embeddings
        if os.path.exists(self.docs_path):
            try:
                with open(self.docs_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.documents = data
                    else:
                        self.documents = data.get("documents", [])
                print(f"✓ Loaded {len(self.documents)} documents from file (text search mode)")
                return
            except Exception as e:
                print(f"Failed to load documents: {e}")
        
        print("✓ Created new FAISS index (empty)")
    
    async def add_documents(self, documents: List[Dict]) -> None:
        """Add documents to vector store."""
        if not documents:
            return
        
        # Extract texts
        texts = [doc.get('content', '') for doc in documents]
        
        # Generate embeddings
        embeddings = await self.model_router.generate_embeddings(texts)
        if not embeddings:
            raise ValueError("Embedding provider returned no embeddings")
        
        # Add to FAISS
        embeddings_array = np.array(embeddings).astype('float32')
        # If embedding dimensions changed, recreate index to avoid FAISS dimension mismatch.
        if embeddings_array.shape[1] != self.embedding_dim:
            self.embedding_dim = int(embeddings_array.shape[1])
            self.index = faiss.IndexFlatL2(self.embedding_dim)
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
            print(f"⚠️  FAISS not available (ntotal={self.index.ntotal if self.index else 'None'}), using text search")
            return self._text_search(query, k)
        
        try:
            # Embed query
            query_embeddings = await self.model_router.generate_embeddings([query])
            if not query_embeddings:
                raise ValueError("Embedding provider returned no query embedding")
            query_array = np.array(query_embeddings).astype('float32')
            
            print(f"🔍 Searching FAISS with query embedding shape: {query_array.shape}")
            print(f"   Index has {self.index.ntotal} vectors with dimension {self.embedding_dim}")
            
            # Search - FAISS returns distances (lower is better for L2)
            distances, indices = self.index.search(query_array, min(k, self.index.ntotal))
            
            print(f"✓ FAISS search returned {len(indices[0])} results")
            
            # Build results with relevance scores
            results = []
            max_distance = np.max(distances[0]) if distances[0].size > 0 else 1.0
            
            for dist, idx in zip(distances[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):
                    # Convert distance to similarity score (0-1)
                    relevance_score = 1.0 - (dist / (max_distance + 1e-6))
                    results.append((self.documents[idx], relevance_score))
            
            print(f"✓ FAISS returned {len(results)} documents")
            return results
        except Exception as e:
            print(f"❌ Embedding search failed: {e}, falling back to text search")
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
                json.dump({"documents": self.documents}, f, indent=2)
            with open(self.metadata_path, "w") as f:
                json.dump(
                    {
                        "embedding_dim": int(self.embedding_dim),
                        "num_vectors": int(self.index.ntotal if self.index is not None else 0),
                        "num_documents": int(len(self.documents)),
                        "index_type": type(self.index).__name__ if self.index is not None else None,
                        "embedding_provider": getattr(settings, "embedding_provider", None),
                        "embedding_model": getattr(settings, "embedding_model", None),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"Warning: Failed to save index: {e}")
    
    def clear(self):
        """Clear the index."""
        self.documents = []
        self.index = faiss.IndexFlatL2(self.embedding_dim)
