"""
Integration tests for the Regulation Navigator RAG system.

Tests the complete end-to-end pipeline:
1. Data loading and parsing
2. TF-IDF vectorization and indexing
3. Retrieval (similarity search)
4. LLM generation
5. HTTP API request/response cycle
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


class TestDataLoading(unittest.TestCase):
    """Test data.txt loading and parsing."""
    
    def test_load_chunks_file_exists(self):
        """Verify data.txt file exists."""
        data_path = Path(__file__).parent.parent / "data.txt"
        self.assertTrue(data_path.exists(), "data.txt file not found")
    
    def test_load_chunks_format(self):
        """Verify data.txt is in correct format."""
        data_path = Path(__file__).parent.parent / "data.txt"
        with open(data_path) as f:
            content = f.read()
        
        # Check for [DOC] headers
        self.assertIn("[DOC]", content, "data.txt should contain [DOC] headers")
        
        # Count chunks (rough estimate)
        chunks = content.count("[DOC]")
        self.assertGreater(chunks, 0, "data.txt should contain at least one chunk")
    
    def test_load_chunks_content(self):
        """Verify loaded chunks have required fields."""
        from app import load_chunks
        
        chunks = load_chunks()
        
        # Verify chunks is a list
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0, "Should load at least one chunk")
        
        # Verify each chunk has required fields
        for chunk in chunks:
            self.assertIn("doc", chunk, "Chunk missing 'doc' field")
            self.assertIn("section", chunk, "Chunk missing 'section' field")
            self.assertIn("text", chunk, "Chunk missing 'text' field")
            
            # Verify fields are non-empty strings
            self.assertIsInstance(chunk["doc"], str)
            self.assertIsInstance(chunk["section"], str)
            self.assertIsInstance(chunk["text"], str)
            self.assertGreater(len(chunk["text"]), 0)


class TestRetrieval(unittest.TestCase):
    """Test TF-IDF retrieval mechanism."""
    
    def setUp(self):
        """Set up test fixtures."""
        from app import VECTORIZER, MATRIX, CHUNKS
        self.vectorizer = VECTORIZER
        self.matrix = MATRIX
        self.chunks = CHUNKS
    
    def test_vectorizer_initialized(self):
        """Verify TF-IDF vectorizer is initialized."""
        self.assertIsNotNone(self.vectorizer)
        self.assertGreater(self.vectorizer.get_feature_names_out().shape[0], 0)
    
    def test_matrix_shape(self):
        """Verify matrix shape matches chunks and vocabulary."""
        num_chunks = len(self.chunks)
        vocab_size = self.vectorizer.get_feature_names_out().shape[0]
        
        self.assertEqual(self.matrix.shape[0], num_chunks)
        self.assertEqual(self.matrix.shape[1], vocab_size)
    
    def test_retrieval_query_processing(self):
        """Test that query vectorization works."""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Test with a realistic question
        question = "What is personal data protection?"
        question_vector = self.vectorizer.transform([question])
        
        # Compute similarity
        similarities = cosine_similarity(question_vector, self.matrix)[0]
        
        # Verify similarities are computed
        self.assertEqual(len(similarities), len(self.chunks))
        
        # Verify similarities are in valid range
        for sim in similarities:
            self.assertGreaterEqual(sim, 0.0)
            self.assertLessEqual(sim, 1.0)
    
    def test_retrieval_ranking(self):
        """Test that chunks are correctly ranked by similarity."""
        from sklearn.metrics.pairwise import cosine_similarity
        
        question = "GDPR personal data"
        question_vector = self.vectorizer.transform([question])
        similarities = cosine_similarity(question_vector, self.matrix)[0]
        
        # Get top-3 indices
        top_k = 3
        top_indices = similarities.argsort()[-top_k:][::-1]
        top_scores = similarities[top_indices]
        
        # Verify ranking (scores should be descending)
        for i in range(len(top_scores) - 1):
            self.assertGreaterEqual(top_scores[i], top_scores[i + 1])


class TestAPIEndpoints(unittest.TestCase):
    """Test HTTP API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        from app import app
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test /health endpoint returns ok."""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
    
    def test_ask_endpoint_exists(self):
        """Test /ask endpoint exists."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 3}
        )
        
        # Should get either 200 (success), 422 (validation), or 502 (LLM unavailable)
        # Should NOT get 404 (endpoint not found)
        self.assertNotEqual(response.status_code, 404)
    
    def test_ask_valid_request(self):
        """Test /ask with valid request (handles LLM unavailability)."""
        response = self.client.post(
            "/ask",
            json={"question": "What is customer due diligence?", "top_k": 3}
        )
        
        # Accept 200 (success) or 502 (LLM API unavailable during test)
        self.assertIn(response.status_code, [200, 502])
        
        # Only check response structure if we got a successful response
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            self.assertIn("answer", data)
            self.assertIn("citations", data)
            self.assertIn("scores", data)
            
            # Verify answer is non-empty
            self.assertIsInstance(data["answer"], str)
            self.assertGreater(len(data["answer"]), 0)
            
            # Verify citations is a list
            self.assertIsInstance(data["citations"], list)
            
            # Verify scores is a list with correct length
            self.assertIsInstance(data["scores"], list)
            self.assertEqual(len(data["scores"]), len(data["citations"]))
    
    def test_ask_missing_question(self):
        """Test /ask with missing question field."""
        response = self.client.post(
            "/ask",
            json={"top_k": 3}
        )
        
        # Should return 422 validation error
        self.assertEqual(response.status_code, 422)
    
    def test_ask_question_too_short(self):
        """Test /ask with question below minimum length."""
        response = self.client.post(
            "/ask",
            json={"question": "hi", "top_k": 3}
        )
        
        # Should return 422 validation error
        self.assertEqual(response.status_code, 422)
    
    def test_ask_top_k_validation(self):
        """Test /ask with invalid top_k values."""
        # Test top_k too large
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 100}
        )
        self.assertEqual(response.status_code, 422)
        
        # Test top_k zero
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 0}
        )
        self.assertEqual(response.status_code, 422)
    
    def test_ask_default_top_k(self):
        """Test /ask with default top_k value."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?"}
        )
        
        # Accept 200 or 502 (LLM unavailable)
        self.assertIn(response.status_code, [200, 502])
        
        if response.status_code == 200:
            data = response.json()
            # Default top_k is 3
            self.assertLessEqual(len(data["citations"]), 3)
    
    def test_ask_response_citations_structure(self):
        """Test that response citations have correct structure."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 3}
        )
        
        # Accept 200 or 502 (LLM unavailable)
        if response.status_code == 200:
            data = response.json()
            
            # Verify each citation has doc and section
            for citation in data.get("citations", []):
                self.assertIn("doc", citation)
                self.assertIn("section", citation)
                self.assertIsInstance(citation["doc"], str)
                self.assertIsInstance(citation["section"], str)


class TestRAGPipeline(unittest.TestCase):
    """Test complete RAG pipeline (retrieval + generation)."""
    
    def setUp(self):
        """Set up test fixtures."""
        from app import app, CHUNKS, VECTORIZER
        self.client = TestClient(app)
        self.chunks = CHUNKS
        self.vectorizer = VECTORIZER
    
    def test_pipeline_question_in_scope(self):
        """Test that in-scope questions return answers (or LLM error)."""
        response = self.client.post(
            "/ask",
            json={"question": "What is personal data?", "top_k": 3}
        )
        
        # Accept 200 (success) or 502 (LLM unavailable during test)
        self.assertIn(response.status_code, [200, 502])
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have a substantial answer
            self.assertGreater(len(data["answer"]), 50)
            
            # Should have citations
            self.assertGreater(len(data["citations"]), 0)
    
    def test_pipeline_preserves_citations(self):
        """Test that citations match retrieved chunks."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 2}
        )
        
        # Skip if LLM unavailable
        if response.status_code == 502:
            self.skipTest("LLM API unavailable")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that returned citations exist in data source
        for citation in data.get("citations", []):
            found = False
            for chunk in self.chunks:
                if (chunk["doc"] == citation["doc"] and 
                    chunk["section"] == citation["section"]):
                    found = True
                    break
            
            self.assertTrue(found, 
                           f"Citation {citation} not found in chunks")
    
    def test_pipeline_retrieval_quality(self):
        """Test that retrieved chunks are relevant to question."""
        response = self.client.post(
            "/ask",
            json={"question": "What is data protection?", "top_k": 3}
        )
        
        # Skip if LLM unavailable
        if response.status_code == 502:
            self.skipTest("LLM API unavailable")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        scores = data.get("scores", [])
        
        # All scores should be non-zero (found relevant chunks)
        for score in scores:
            self.assertGreater(score, 0)
        
        # Scores should be sorted descending
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(scores[i], scores[i + 1])


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test client."""
        from app import app
        self.client = TestClient(app)
    
    def test_ask_with_special_characters(self):
        """Test /ask with special characters in question."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR? (General Data Protection)", "top_k": 3}
        )
        
        # Should handle special characters gracefully (200 or 502 for LLM)
        self.assertIn(response.status_code, [200, 422, 502])
    
    def test_ask_with_very_long_question(self):
        """Test /ask with very long question."""
        long_question = "What " * 200  # Create a long question (1000+ chars)
        
        response = self.client.post(
            "/ask",
            json={"question": long_question, "top_k": 3}
        )
        
        # Should return validation error (422) or LLM error (502)
        # since long question may exceed token limits
        self.assertIn(response.status_code, [422, 502])
    
    def test_ask_with_unicode_question(self):
        """Test /ask with unicode characters."""
        response = self.client.post(
            "/ask",
            json={"question": "What is Datenschutz? (German for data protection)", "top_k": 3}
        )
        
        # Should handle unicode gracefully (200 or 502 for LLM)
        self.assertIn(response.status_code, [200, 502])
    
    def test_api_content_type(self):
        """Test that API returns JSON content type."""
        response = self.client.post(
            "/ask",
            json={"question": "What is GDPR?", "top_k": 3}
        )
        
        self.assertEqual(response.headers["content-type"], "application/json")


class TestDataConsistency(unittest.TestCase):
    """Test data consistency and integrity."""
    
    def test_chunks_no_duplicates(self):
        """Verify chunks are unique."""
        from app import CHUNKS
        
        seen = set()
        for chunk in CHUNKS:
            # Create a unique identifier from chunk content
            identifier = (chunk["doc"], chunk["section"])
            
            self.assertNotIn(identifier, seen,
                           f"Duplicate chunk found: {identifier}")
            seen.add(identifier)
    
    def test_chunks_non_empty_text(self):
        """Verify all chunks have non-empty text."""
        from app import CHUNKS
        
        for i, chunk in enumerate(CHUNKS):
            self.assertGreater(len(chunk["text"]), 30,
                             f"Chunk {i} has text too short: {len(chunk['text'])} chars")
    
    def test_chunks_minimal_metadata(self):
        """Verify all chunks have required metadata."""
        from app import CHUNKS
        
        for i, chunk in enumerate(CHUNKS):
            self.assertGreater(len(chunk["doc"]), 0,
                             f"Chunk {i} has empty doc")
            self.assertGreater(len(chunk["section"]), 0,
                             f"Chunk {i} has empty section")
            
            # Verify format (should look like regulation or directive names)
            # Accept both "Regulation" and "Directive"
            self.assertTrue(
                "Regulation" in chunk["doc"] or "Directive" in chunk["doc"],
                f"Chunk {i} doesn't look like a valid regulation/directive"
            )


def run_integration_tests():
    """Run all integration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestDataLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestRetrieval))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestRAGPipeline))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestDataConsistency))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_integration_tests()
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
