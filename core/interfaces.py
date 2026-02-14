"""
Core abstractions for retrieval and synthesis.

These interfaces define contracts that implementations must follow.
Follows Interface Segregation and Dependency Inversion principles.
"""

from abc import ABC, abstractmethod
from typing import List
from core.entities import RegulatoryChunk, ComplianceQuestion


class RetrievalEngine(ABC):
    """Abstract retrieval engine.
    
    Single Responsibility: Only responsible for finding relevant chunks.
    
    Implementations must provide efficient similarity matching and ranking.
    """
    
    @abstractmethod
    def index_chunks(self, chunks: List[RegulatoryChunk]) -> None:
        """Build index from regulatory chunks.
        
        Args:
            chunks: List of regulatory document chunks to index
            
        Raises:
            ValueError: If chunks are invalid or empty
        """
        raise NotImplementedError
    
    @abstractmethod
    def retrieve(self, question: str, top_k: int) -> tuple[List[RegulatoryChunk], List[float]]:
        """Retrieve top-k relevant chunks for a question.
        
        Args:
            question: The compliance question
            top_k: Number of results to return
            
        Returns:
            Tuple of (chunks, similarity_scores)
            
        Raises:
            ValueError: If question is empty or top_k is invalid
        """
        raise NotImplementedError
    
    @abstractmethod
    def is_question_in_scope(self, question: str, threshold: float = 0.05) -> bool:
        """Check if question is within document scope.
        
        Args:
            question: The question to check
            threshold: Similarity threshold for relevance
            
        Returns:
            True if question matches documents above threshold
        """
        raise NotImplementedError


class LanguageModel(ABC):
    """Abstract language model for synthesis.
    
    Single Responsibility: Only responsible for generating answers from context.
    
    Implementations handle different LLM providers (OpenAI, Anthropic, etc).
    """
    
    @abstractmethod
    def generate_answer(self, question: str, context: str) -> str:
        """Generate a compliance answer based on question and context.
        
        Args:
            question: The compliance question
            context: Retrieved regulatory text as context
            
        Returns:
            Generated answer grounded in the context
            
        Raises:
            RuntimeError: If LLM service is unavailable
        """
        raise NotImplementedError


class DataLoader(ABC):
    """Abstract data loader for regulatory documents.
    
    Single Responsibility: Only responsible for loading and parsing data.
    
    Implementations can load from files, APIs, databases, etc.
    """
    
    @abstractmethod
    def load(self, source: str) -> List[RegulatoryChunk]:
        """Load regulatory chunks from a source.
        
        Args:
            source: Path, URL, or identifier for the data source
            
        Returns:
            List of parsed regulatory chunks
            
        Raises:
            FileNotFoundError: If source doesn't exist
            ValueError: If data is malformed
        """
        raise NotImplementedError
