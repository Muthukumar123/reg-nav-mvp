#!/usr/bin/env python3
"""
Test script to verify the EU Banking Regulator LLM system is working correctly.
This script tests the system WITHOUT requiring actual API keys by testing
the core components independently.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("✓ Testing imports...")
    try:
        from src.config import settings
        from src.models import (
            QueryRequest, ComplianceCheckRequest, RegulationType,
            ComplianceStatus, DocumentIngestionRequest
        )
        from src.services.vector_db_service import VectorDBService
        from src.services.document_service import DocumentIngestionService
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_models():
    """Test data model creation."""
    print("\n✓ Testing data models...")
    try:
        from src.models import QueryRequest, RegulationType
        
        request = QueryRequest(
            question="What are capital requirements?",
            regulation_types=[RegulationType.CRR],
            include_references=True
        )
        assert request.question == "What are capital requirements?"
        assert RegulationType.CRR in request.regulation_types
        print("  ✓ QueryRequest model works")
        
        from src.models import ComplianceCheckRequest
        comp_request = ComplianceCheckRequest(
            scenario="Test scenario",
            detailed_analysis=True
        )
        assert comp_request.scenario == "Test scenario"
        print("  ✓ ComplianceCheckRequest model works")
        
        return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\n✓ Testing configuration...")
    try:
        from src.config import settings
        
        assert settings.llm_provider in ["openai", "anthropic"]
        assert settings.llm_temperature >= 0 and settings.llm_temperature <= 1
        assert settings.api_port > 0
        print(f"  ✓ Configuration loaded successfully")
        print(f"    - LLM Provider: {settings.llm_provider}")
        print(f"    - LLM Model: {settings.llm_model}")
        print(f"    - Temperature: {settings.llm_temperature}")
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_vector_db():
    """Test vector database initialization."""
    print("\n✓ Testing vector database...")
    try:
        from src.services.vector_db_service import VectorDBService
        
        # This will create the vector DB directory if it doesn't exist
        db_service = VectorDBService()
        stats = db_service.get_collection_stats()
        
        print(f"  ✓ Vector database initialized")
        print(f"    - Total documents: {stats['total_documents']}")
        print(f"    - Embedding model: {stats['embedding_model']}")
        print(f"    - Collection: {stats['collection_name']}")
        return True
    except Exception as e:
        print(f"  ✗ Vector database test failed: {e}")
        return False


def test_document_processing():
    """Test document processing capabilities."""
    print("\n✓ Testing document processing...")
    try:
        from src.services.document_service import DocumentIngestionService
        
        service = DocumentIngestionService()
        
        # Test text chunking
        test_text = "This is a test paragraph.\n\nThis is another paragraph.\n\nAnd a third one."
        chunks = service._chunk_text(test_text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
        
        print(f"  ✓ Document processing works")
        print(f"    - Test text chunked into {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"  ✗ Document processing test failed: {e}")
        return False


def test_seed_data():
    """Test seed data can be loaded."""
    print("\n✓ Testing seed data loading...")
    try:
        from src.utils.seed_data import SAMPLE_REGULATIONS
        
        assert len(SAMPLE_REGULATIONS) > 0
        
        # Check first regulation has required fields
        first_reg = SAMPLE_REGULATIONS[0]
        assert "title" in first_reg
        assert "regulation_type" in first_reg
        assert "content" in first_reg
        
        print(f"  ✓ Seed data structure is valid")
        print(f"    - {len(SAMPLE_REGULATIONS)} sample regulations available")
        return True
    except Exception as e:
        print(f"  ✗ Seed data test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("EU Banking Regulator LLM - System Verification")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Data Models", test_models),
        ("Configuration", test_configuration),
        ("Vector Database", test_vector_db),
        ("Document Processing", test_document_processing),
        ("Seed Data", test_seed_data),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Tests: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Add your API key to .env file")
        print("2. Run: python -m src.utils.seed_data")
        print("3. Start API: python -m src.api.main")
        print("4. Try CLI: python cli.py query")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
