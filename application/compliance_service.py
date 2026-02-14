"""
Compliance service - orchestration layer.

Application-level business logic that coordinates retrieval and synthesis.
Depends on abstractions, not concrete implementations (Dependency Inversion).
"""

import logging
from typing import List

from core.entities import (
    RegulatoryChunk, ComplianceQuestion, ComplianceAnswer, Citation
)
from core.interfaces import RetrievalEngine, LanguageModel, DataLoader

logger = logging.getLogger(__name__)


class ComplianceService:
    """Orchestrates compliance question answering.
    
    - Single Responsibility: Only coordinates retrieval and synthesis
    - Dependency Inversion: Depends on interfaces, not implementations
    - Easy to test: Can inject mock retrieval/LLM
    - Easy to extend: Can swap implementations without changing service
    """
    
    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        language_model: LanguageModel,
        data_loader: DataLoader
    ):
        """Initialize service with dependencies.
        
        Args:
            retrieval_engine: Implementation of RetrievalEngine (TF-IDF, embeddings, etc)
            language_model: Implementation of LanguageModel (Azure, OpenAI, Anthropic, etc)
            data_loader: Implementation of DataLoader (file, API, database, etc)
        """
        self.retrieval_engine = retrieval_engine
        self.language_model = language_model
        self.data_loader = data_loader
        self._initialized = False
        
        logger.info("ComplianceService initialized")
    
    def initialize(self, data_source: str) -> None:
        """Initialize service by loading and indexing data.
        
        Args:
            data_source: Path to regulatory data file
            
        Raises:
            FileNotFoundError: If data source not found
            ValueError: If data is invalid
        """
        logger.info(f"Initializing ComplianceService with data from {data_source}")
        
        try:
            # Load data using DataLoader
            chunks = self.data_loader.load(data_source)
            
            if not chunks:
                raise ValueError("No regulatory chunks loaded")
            
            # Index data using RetrievalEngine
            self.retrieval_engine.index_chunks(chunks)
            self._initialized = True
            
            logger.info(f"Service initialized with {len(chunks)} regulatory chunks")
            
        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            raise
    
    def answer_question(self, question: ComplianceQuestion) -> ComplianceAnswer:
        """Answer a compliance question with citations.
        
        This is the main business logic:
        1. Check if question is in scope
        2. Retrieve relevant regulatory chunks
        3. Synthesize answer using LLM
        4. Format with citations
        
        Args:
            question: ComplianceQuestion object
            
        Returns:
            ComplianceAnswer with sources and scores
            
        Raises:
            ValueError: If question is invalid or out of scope
            RuntimeError: If retrieval or synthesis fails
        """
        if not self._initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")
        
        logger.info(f"Processing question: {question.question[:100]}...")
        
        try:
            # Step 1: Check if question is in scope
            if not self._is_question_relevant(question.question):
                logger.info("Question is out of scope, rejecting")
                return ComplianceAnswer(
                    answer="NOT FOUND IN SOURCES.",
                    citations=[],
                    scores=[]
                )
            
            # Step 2: Retrieve relevant chunks
            chunks, scores = self.retrieval_engine.retrieve(question.question, question.top_k)
            
            # Step 3: Check if we found anything
            if not chunks or not scores:
                logger.info("No relevant sources found")
                return ComplianceAnswer(
                    answer="NOT FOUND IN SOURCES.",
                    citations=[],
                    scores=[]
                )
            
            # Step 4: Build context from retrieved chunks
            context = self._build_context(chunks)
            
            # Step 5: Generate answer using LLM
            answer_text = self.language_model.generate_answer(question.question, context)
            
            # Step 6: Format citations
            citations = [Citation(doc=chunk.doc, section=chunk.section) for chunk in chunks]
            
            # Step 7: Return structured answer
            return ComplianceAnswer(
                answer=answer_text,
                citations=citations,
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            raise
    
    def _is_question_relevant(self, question: str) -> bool:
        """Check if question is relevant to regulatory documents.
        
        Args:
            question: The question to check
            
        Returns:
            True if question matches documents
        """
        return self.retrieval_engine.is_question_in_scope(question, threshold=0.05)
    
    def _build_context(self, chunks: List[RegulatoryChunk]) -> str:
        """Build formatted context string from chunks.
        
        Args:
            chunks: List of relevant chunks
            
        Returns:
            Formatted context for LLM
        """
        context_parts = []
        for chunk in chunks:
            formatted = f"[{chunk.doc} | {chunk.section}]\n{chunk.text.strip()}"
            context_parts.append(formatted)
        
        return "\n\n".join(context_parts)
