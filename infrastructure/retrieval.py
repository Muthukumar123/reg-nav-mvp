"""
TF-IDF retrieval engine implementation.

Concrete implementation of RetrievalEngine interface.
Can be swapped out with embeddings model without affecting rest of system.
"""

import logging
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from core.interfaces import RetrievalEngine
from core.entities import RegulatoryChunk

logger = logging.getLogger(__name__)


class TfidfRetrievalEngine(RetrievalEngine):
    """TF-IDF based retrieval engine.
    
    - Single Responsibility: Only handles TF-IDF retrieval logic
    - Open/Closed: Can be extended without modifying core engine code
    - Easily replaceable with semantic embeddings later
    """
    
    def __init__(self, min_similarity_threshold: float = 0.05):
        """Initialize retrieval engine.
        
        Args:
            min_similarity_threshold: Minimum similarity score to consider relevant
        """
        self.vectorizer = None
        self.matrix = None
        self.chunks = []
        self.min_similarity_threshold = min_similarity_threshold
        self._is_indexed = False
        
        logger.info(f"TfidfRetrievalEngine initialized (threshold={min_similarity_threshold})")
    
    def index_chunks(self, chunks: List[RegulatoryChunk]) -> None:
        """Build TF-IDF index from chunks.
        
        Args:
            chunks: List of regulatory chunks to index
            
        Raises:
            ValueError: If chunks list is empty or invalid
        """
        if not chunks:
            raise ValueError("Cannot index empty chunk list")
        
        logger.info(f"Indexing {len(chunks)} regulatory chunks")
        self.chunks = chunks
        
        try:
            # Initialize vectorizer with optimized settings
            self.vectorizer = TfidfVectorizer(
                stop_words=None,         # Keep all regulatory terms
                min_df=1,                # Accept rare terms
                analyzer='word',
                lowercase=True,
                token_pattern=r'(?u)\b\w+\b'
            )
            
            # Build matrix from chunk texts
            chunk_texts = [chunk.text for chunk in chunks]
            self.matrix = self.vectorizer.fit_transform(chunk_texts)
            
            self._is_indexed = True
            vocab_size = len(self.vectorizer.get_feature_names_out())
            logger.info(f"Index built: {self.matrix.shape[0]} docs, {vocab_size} vocabulary terms")
            
        except Exception as e:
            logger.error(f"Failed to index chunks: {str(e)}")
            raise
    
    def retrieve(self, question: str, top_k: int) -> tuple[List[RegulatoryChunk], List[float]]:
        """Retrieve top-k relevant chunks for a question.
        
        Args:
            question: The compliance question
            top_k: Number of results
            
        Returns:
            Tuple of (relevant_chunks, similarity_scores)
            
        Raises:
            ValueError: If not indexed or invalid input
        """
        if not self._is_indexed:
            raise ValueError("Engine not indexed. Call index_chunks first.")
        
        if not question or len(question.strip()) == 0:
            raise ValueError("Question cannot be empty")
        
        if top_k < 1 or top_k > len(self.chunks):
            raise ValueError(f"top_k must be between 1 and {len(self.chunks)}")
        
        try:
            # Transform question using fitted vectorizer
            question_vector = self.vectorizer.transform([question])
            
            # Compute similarities
            similarities = cosine_similarity(question_vector, self.matrix).flatten()
            
            # Get sorted indices
            sorted_indices = similarities.argsort()[::-1]
            
            # Filter by threshold and limit to top_k
            relevant_indices = [
                i for i in sorted_indices 
                if similarities[i] > self.min_similarity_threshold
            ][:top_k]
            
            # Extract chunks and scores
            relevant_chunks = [self.chunks[i] for i in relevant_indices]
            relevant_scores = [float(similarities[i]) for i in relevant_indices]
            
            logger.debug(f"Retrieved {len(relevant_chunks)} chunks for question (scores: {relevant_scores})")
            
            return relevant_chunks, relevant_scores
            
        except Exception as e:
            logger.error(f"Retrieval failed: {str(e)}")
            raise
    
    def is_question_in_scope(self, question: str, threshold: float = 0.05) -> bool:
        """Check if question has relevant matches.
        
        Args:
            question: The question to check
            threshold: Similarity threshold
            
        Returns:
            True if best match exceeds threshold
        """
        if not self._is_indexed or not question:
            return False
        
        try:
            chunks, scores = self.retrieve(question, top_k=1)
            if not scores:
                return False
            return scores[0] >= threshold
        except:
            return False
