"""Vector store using FAISS for similarity search."""

import json
import logging
import os
import pickle
import time
from typing import Optional

import numpy as np
from app.config import settings
from app.llm import model_router
from app.observability import tracer

logger = logging.getLogger(__name__)

try:
    import faiss
except ImportError:
    faiss = None


class VectorStore:
    """FAISS-based vector store for document retrieval."""

    def __init__(self, index_path: Optional[str] = None):
        """Initialize vector store.

        Args:
            index_path: Path to save/load FAISS index
        """
        if faiss is None:
            logger.warning("FAISS not installed. Vector search will be unavailable.")

        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.embeddings_cache_path = settings.EMBEDDINGS_CACHE_PATH
        self.index: Optional[faiss.IndexFlatL2] = None
        self.documents: list[dict] = []
        self.embeddings: list[np.ndarray] = []

        self._initialize_index()

    def _initialize_index(self) -> None:
        """Initialize or load FAISS index."""
        if os.path.exists(self.index_path) and os.path.exists(self.embeddings_cache_path):
            self._load_index()
        else:
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Create a new FAISS index with sample data."""
        if faiss is None:
            logger.warning("Cannot create FAISS index - FAISS not installed")
            return

        # Sample technical documents for demonstration
        sample_docs = [
            {
                "id": "1",
                "text": "Artificial Intelligence (AI) is the simulation of human intelligence processes by computer systems. These processes include learning, reasoning, and self-correction.",
                "source": "https://example.com/ai-basics",
                "title": "AI Basics",
            },
            {
                "id": "2",
                "text": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without explicit programming.",
                "source": "https://example.com/ml-intro",
                "title": "Machine Learning Introduction",
            },
            {
                "id": "3",
                "text": "Natural Language Processing (NLP) is a branch of AI that focuses on enabling computers to understand and process human language.",
                "source": "https://example.com/nlp-guide",
                "title": "NLP Guide",
            },
            {
                "id": "4",
                "text": "Deep Learning utilizes neural networks with multiple layers to process complex patterns in data.",
                "source": "https://example.com/deep-learning",
                "title": "Deep Learning Overview",
            },
            {
                "id": "5",
                "text": "Transformers are neural network architectures that rely on self-attention mechanisms for processing sequential data.",
                "source": "https://example.com/transformers",
                "title": "Transformers Explained",
            },
            {
                "id": "6",
                "text": "Large Language Models (LLMs) are deep learning models trained on vast amounts of text data to understand and generate human language.",
                "source": "https://example.com/llm-guide",
                "title": "Large Language Models",
            },
            {
                "id": "7",
                "text": "Retrieval Augmented Generation (RAG) combines document retrieval with language generation to provide contextually grounded responses.",
                "source": "https://example.com/rag-explained",
                "title": "RAG Explanation",
            },
            {
                "id": "8",
                "text": "Embeddings are vector representations of text that capture semantic meaning, useful for similarity search and clustering.",
                "source": "https://example.com/embeddings",
                "title": "Vector Embeddings",
            },
        ]

        self.documents = sample_docs
        self._generate_and_store_embeddings()

    def _generate_and_store_embeddings(self) -> None:
        """Generate embeddings for all documents."""
        if faiss is None:
            return

        texts = [doc["text"] for doc in self.documents]

        # Generate embeddings (stub - would use OpenAI in production)
        import asyncio

        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        embeddings = loop.run_until_complete(model_router.get_embeddings(texts))

        if not embeddings:
            logger.warning("Failed to generate embeddings, using random vectors")
            embeddings = [np.random.randn(1536).astype("float32") for _ in texts]
        else:
            embeddings = [np.array(e, dtype="float32") for e in embeddings]

        self.embeddings = embeddings

        # Create FAISS index
        embedding_dim = len(embeddings[0]) if embeddings else 1536
        self.index = faiss.IndexFlatL2(embedding_dim)

        vectors = np.vstack(embeddings)
        self.index.add(vectors)

        # Save index and cache
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)

        with open(self.embeddings_cache_path, "w") as f:
            json.dump(
                {
                    "documents": self.documents,
                    "embeddings": [e.tolist() for e in embeddings],
                },
                f,
            )

        logger.info(f"Created FAISS index with {len(self.documents)} documents")

    def _load_index(self) -> None:
        """Load existing FAISS index."""
        if faiss is None:
            return

        try:
            self.index = faiss.read_index(self.index_path)

            with open(self.embeddings_cache_path, "r") as f:
                cache = json.load(f)
                self.documents = cache["documents"]
                self.embeddings = [np.array(e, dtype="float32") for e in cache["embeddings"]]

            logger.info(f"Loaded FAISS index with {len(self.documents)} documents")

        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            self._create_new_index()

    async def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant documents with scores
        """
        if faiss is None or not self.index:
            logger.warning("Vector search not available")
            return []

        start_time = time.time()

        try:
            # Get query embedding
            query_embeddings = await model_router.get_embeddings([query])
            if not query_embeddings:
                return []

            query_vector = np.array(query_embeddings[0], dtype="float32").reshape(1, -1)

            # Search
            distances, indices = self.index.search(query_vector, min(top_k, len(self.documents)))

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < 0 or idx >= len(self.documents):
                    continue

                doc = self.documents[idx]
                # Convert L2 distance to similarity score (0-1)
                distance = distances[0][i]
                similarity = 1 / (1 + distance)

                results.append({
                    **doc,
                    "relevance_score": similarity,
                })

            latency_ms = (time.time() - start_time) * 1000
            tracer.trace_retrieval(query, len(results), results, latency_ms)

            logger.info(f"Vector search returned {len(results)} results in {latency_ms:.2f}ms")

            return results

        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            return []

    def add_documents(self, documents: list[dict]) -> None:
        """Add new documents to the vector store.

        Args:
            documents: List of documents to add
        """
        if faiss is None:
            return

        self.documents.extend(documents)
        self._generate_and_store_embeddings()


# Global vector store instance
vector_store = VectorStore()
