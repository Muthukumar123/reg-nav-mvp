"""
Domain entities and value objects.

These represent core business concepts with no dependencies on frameworks or infrastructure.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RegulatoryChunk:
    """Represents a single chunk from a regulatory document.
    
    Pure domain entity - no FastAPI, database, or infrastructure concerns.
    """
    doc: str              # Document name (e.g., "EU Directive 2015/849")
    section: str          # Article/section (e.g., "Article 5 - Customer Due Diligence")
    text: str             # Raw text content
    
    def __post_init__(self):
        """Validate entity invariants."""
        if not self.doc or not self.section or len(self.text) < 30:
            raise ValueError("Invalid RegulatoryChunk: missing required fields or insufficient text")


@dataclass
class ComplianceQuestion:
    """Represents a user's compliance question.
    
    Pure value object with validation.
    """
    question: str       # The compliance question
    top_k: int = 3      # Number of sources to retrieve
    
    def __post_init__(self):
        """Validate question invariants."""
        if not self.question or len(self.question.strip()) == 0:
            raise ValueError("Question cannot be empty")
        if self.top_k < 1 or self.top_k > 10:
            raise ValueError("top_k must be between 1 and 10")


@dataclass
class Citation:
    """Represents a citation to a regulatory source.
    
    Immutable value object.
    """
    doc: str        # Document identifier
    section: str    # Section/article reference
    
    def __str__(self) -> str:
        return f"{self.doc} | {self.section}"


@dataclass
class ComplianceAnswer:
    """Represents a complete compliance answer with citations.
    
    Pure domain object - the main output of our system.
    """
    answer: str                      # The generated compliance answer
    citations: List[Citation]        # Sources used
    scores: List[float]              # Similarity scores for each source
    
    def __post_init__(self):
        """Validate answer invariants."""
        if not self.answer:
            raise ValueError("Answer cannot be empty")
        if len(self.citations) != len(self.scores):
            raise ValueError("Citations and scores must have same length")
        if any(score < 0 or score > 1 for score in self.scores):
            raise ValueError("Scores must be between 0 and 1")
