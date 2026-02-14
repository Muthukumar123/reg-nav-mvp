"""Tests for the EU Banking Regulator LLM system."""
import pytest
from datetime import datetime

from src.models import (
    QueryRequest,
    ComplianceCheckRequest,
    RegulationType,
    DocumentIngestionRequest,
    ComplianceStatus
)


class TestModels:
    """Test data models."""
    
    def test_query_request_creation(self):
        """Test QueryRequest model creation."""
        request = QueryRequest(
            question="What are capital requirements?",
            regulation_types=[RegulationType.CRR],
            include_references=True,
            max_results=5
        )
        
        assert request.question == "What are capital requirements?"
        assert len(request.regulation_types) == 1
        assert request.include_references is True
        assert request.max_results == 5
    
    def test_compliance_check_request_creation(self):
        """Test ComplianceCheckRequest model creation."""
        request = ComplianceCheckRequest(
            scenario="A bank wants to process customer data",
            regulation_types=[RegulationType.GDPR],
            detailed_analysis=True
        )
        
        assert "customer data" in request.scenario
        assert RegulationType.GDPR in request.regulation_types
        assert request.detailed_analysis is True
    
    def test_regulation_types(self):
        """Test regulation type enum."""
        assert RegulationType.CRR.value == "Capital Requirements Regulation"
        assert RegulationType.GDPR.value == "General Data Protection Regulation"
        assert RegulationType.MiFID.value == "Markets in Financial Instruments Directive"
    
    def test_compliance_status_enum(self):
        """Test compliance status enum."""
        assert ComplianceStatus.COMPLIANT.value == "compliant"
        assert ComplianceStatus.NON_COMPLIANT.value == "non_compliant"
        assert ComplianceStatus.PARTIALLY_COMPLIANT.value == "partially_compliant"


class TestVectorDBService:
    """Test vector database service."""
    
    def test_chunking_logic(self):
        """Test text chunking logic."""
        from src.services.document_service import DocumentIngestionService
        
        service = DocumentIngestionService()
        
        # Test with simple text
        text = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
        chunks = service._chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_text_extraction(self):
        """Test text extraction from different file types."""
        from src.services.document_service import DocumentIngestionService
        
        service = DocumentIngestionService()
        
        # Test with unsupported file type
        with pytest.raises(ValueError):
            service._extract_text("test.xyz")


class TestConfiguration:
    """Test configuration management."""
    
    def test_settings_defaults(self):
        """Test default settings."""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.llm_provider == "openai"
        assert settings.llm_temperature == 0.3
        assert settings.llm_max_tokens == 4096
        assert settings.api_port == 8000


@pytest.mark.asyncio
class TestRAGService:
    """Test RAG service (requires LLM setup)."""
    
    async def test_confidence_calculation(self):
        """Test confidence score calculation."""
        from src.services.rag_service import RAGService
        
        service = RAGService()
        
        # Test with sample distances
        distances = [0.1, 0.2, 0.3]
        confidence = service._calculate_confidence(distances)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    async def test_context_building(self):
        """Test context building from documents."""
        from src.services.rag_service import RAGService
        
        service = RAGService()
        
        documents = ["Document 1 content", "Document 2 content"]
        metadatas = [
            {"title": "Doc 1", "regulation_type": "CRR"},
            {"title": "Doc 2", "regulation_type": "GDPR"}
        ]
        
        context = service._build_context(documents, metadatas)
        
        assert "Doc 1" in context
        assert "Doc 2" in context
        assert "Document 1 content" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
