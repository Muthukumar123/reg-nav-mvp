"""Vector database service for storing and retrieving regulatory documents."""
import os
import logging
from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from src.config import settings

logger = logging.getLogger(__name__)


class VectorDBService:
    """Service for managing the vector database."""
    
    def __init__(self):
        """Initialize the vector database service."""
        # Ensure directory exists
        os.makedirs(settings.vector_db_path, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=settings.vector_db_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="regulatory_documents",
            metadata={"description": "EU Banking Regulatory Documents"}
        )
        
        logger.info(f"Initialized VectorDB at: {settings.vector_db_path}")
        logger.info(f"Collection size: {self.collection.count()}")
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to the vector database."""
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(texts)} documents to vector database")
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search the collection
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=filter_metadata
        )
        
        return results
    
    def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from the vector database."""
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from vector database")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        return {
            "total_documents": self.collection.count(),
            "embedding_model": settings.embedding_model,
            "collection_name": self.collection.name
        }
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.client.delete_collection(name="regulatory_documents")
        self.collection = self.client.get_or_create_collection(
            name="regulatory_documents",
            metadata={"description": "EU Banking Regulatory Documents"}
        )
        logger.info("Cleared all documents from vector database")


# Global vector database service instance
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db_service() -> VectorDBService:
    """Get or create the global vector database service instance."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service
