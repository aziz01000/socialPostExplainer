#!/usr/bin/env python3
"""
Populate FAISS vector database with embeddings.

This script:
1. Loads documents from documents.json
2. Generates embeddings for each document
3. Creates FAISS index
4. Saves index and documents to disk
"""

import sys
import os
import json
import faiss
import numpy as np
from pathlib import Path
import asyncio

# Add parent directory (backend) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.model_router import ModelRouter
from app.config import settings


async def populate_faiss_db(
    docs_file: str = None,
    output_dir: str = None
) -> dict:
    """
    Create and populate FAISS index with embeddings.
    
    Args:
        docs_file: Path to documents.json (default: data/documents.json)
        output_dir: Directory to save FAISS index (default: data)
    
    Returns:
        Statistics dict with counts and info
    """
    # Use default paths relative to backend directory
    if docs_file is None:
        docs_file = os.path.join(os.path.dirname(__file__), "..", "data", "documents.json")
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    print("🔄 Loading documents...")
    
    # Load documents
    if not os.path.exists(docs_file):
        print(f"❌ File not found: {docs_file}")
        return {}
    
    with open(docs_file, 'r') as f:
        data = json.load(f)
        documents = data.get("documents", [])
    
    print(f"✓ Loaded {len(documents)} documents")
    
    if not documents:
        print("❌ No documents to process")
        return {}
    
    # Initialize model router for embeddings
    model_router = ModelRouter()
    embedding_dim = 1536  # text-embedding-3-small dimension
    
    print(f"\n🔄 Generating embeddings for {len(documents)} documents...")
    print(f"   Using provider: {settings.llm_provider}")
    print(f"   Using model: {settings.openai_model if settings.llm_provider == 'openai' else settings.gemini_model}")
    
    try:
        # Extract texts to embed
        texts = [doc.get("content", "") for doc in documents]
        
        # Generate embeddings
        embeddings = await model_router.generate_embeddings(texts)
        print(f"✓ Generated {len(embeddings)} embeddings")
        
        # Verify all embeddings
        if not embeddings or len(embeddings) != len(documents):
            print(f"❌ Embedding count mismatch: got {len(embeddings)}, expected {len(documents)}")
            return {}
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        print(f"✓ Embeddings shape: {embeddings_array.shape}")
        
        # Verify embedding dimension
        if embeddings_array.shape[1] != embedding_dim:
            print(f"⚠️  Embedding dimension mismatch: {embeddings_array.shape[1]} vs {embedding_dim}")
            embedding_dim = embeddings_array.shape[1]
        
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        print("   Falling back to text-based search only")
        return {
            "success": False,
            "error": str(e),
            "documents_count": len(documents),
            "method": "text-search-only"
        }
    
    print("\n🔄 Creating FAISS index...")
    
    # Create FAISS index
    # Using L2 distance (Euclidean)
    index = faiss.IndexFlatL2(embedding_dim)
    
    # Add vectors to index
    index.add(embeddings_array)
    print(f"✓ Added {index.ntotal} vectors to FAISS index")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save FAISS index
    index_path = os.path.join(output_dir, "faiss.index")
    faiss.write_index(index, index_path)
    print(f"✓ Saved FAISS index to: {index_path}")
    
    # Save documents for reference
    docs_output_path = os.path.join(output_dir, "documents.json")
    with open(docs_output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✓ Saved documents to: {docs_output_path}")
    
    # Save metadata
    metadata = {
        "embedding_dim": embedding_dim,
        "num_vectors": index.ntotal,
        "num_documents": len(documents),
        "index_type": "IndexFlatL2",
        "provider": settings.llm_provider,
        "model": settings.openai_model if settings.llm_provider == "openai" else settings.gemini_model,
    }
    
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Saved metadata to: {metadata_path}")
    
    print("\n✅ FAISS Vector Database Created Successfully!")
    print("\n📊 Statistics:")
    for key, value in metadata.items():
        print(f"   {key}: {value}")
    
    return {
        "success": True,
        "index_path": index_path,
        "documents_count": len(documents),
        "embedding_dim": embedding_dim,
        "method": "semantic-search"
    }


async def test_search(
    index_dir: str = None,
    query: str = "What is embedding?"
) -> None:
    """Test the FAISS index with a sample query."""
    # Use default path relative to backend directory
    if index_dir is None:
        index_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    
    print(f"\n🔍 Testing search with query: '{query}'")
    
    # Load index
    index_path = os.path.join(index_dir, "faiss.index")
    docs_path = os.path.join(index_dir, "documents.json")
    metadata_path = os.path.join(index_dir, "metadata.json")
    
    if not os.path.exists(index_path):
        print(f"❌ Index not found at {index_path}")
        return
    
    # Load components
    index = faiss.read_index(index_path)
    
    with open(docs_path, 'r') as f:
        data = json.load(f)
        documents = data.get("documents", [])
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"✓ Loaded index with {index.ntotal} vectors")
    
    try:
        # Generate query embedding
        model_router = ModelRouter()
        query_embeddings = await model_router.generate_embeddings([query])
        query_array = np.array(query_embeddings).astype('float32')
        
        # Search
        k = 3
        distances, indices = index.search(query_array, k)
        
        print(f"\n📊 Top {k} search results:")
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(documents):
                doc = documents[idx]
                relevance = 1.0 - (dist / (np.max(distances[0]) + 1e-6))
                print(f"\n   {i+1}. {doc['title']}")
                print(f"      Similarity: {relevance:.2%}")
                print(f"      Content: {doc['content'][:100]}...")
    
    except Exception as e:
        print(f"❌ Search failed: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate FAISS vector database")
    parser.add_argument("--docs", default=None, help="Path to documents.json (default: data/documents.json)")
    parser.add_argument("--output", default=None, help="Output directory for FAISS index (default: data)")
    parser.add_argument("--test", action="store_true", help="Test the index after creation")
    parser.add_argument("--query", default="What is embedding?", help="Test query")
    
    args = parser.parse_args()
    
    # Run population
    result = asyncio.run(populate_faiss_db(args.docs, args.output))
    
    if args.test and result.get("success"):
        asyncio.run(test_search(args.output, args.query))


if __name__ == "__main__":
    main()
