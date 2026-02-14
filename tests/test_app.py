"""Application Integration Tests

Comprehensive test suite for the Regulation Navigator FastAPI application.
Tests cover:
- Data loading and document chunk parsing
- System health checks
- API endpoint functionality (GET /, GET /health, POST /ask)
- Request validation and error handling
- LLM integration and mocking
- TF-IDF retrieval accuracy
- Citation tracking and similarity scoring

Test Coverage:
- 3 data loading tests
- 1 health check test
- 8 /ask endpoint tests
- 2 retrieval mechanism tests

Run with: python -m unittest tests.test_app -v
"""

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app import app, load_chunks, CHUNKS, VECTORIZER, MATRIX


class TestDataLoading(unittest.TestCase):
    """Test data loading and initialization."""
    
    def test_load_chunks_from_data_file(self):
        """Test that chunks are loaded and parsed correctly from data.txt"""
        chunks = load_chunks("data.txt")
        self.assertGreater(len(chunks), 0, "Should load at least one chunk")
        
        # Check structure of chunks
        for chunk in chunks:
            self.assertIn("doc", chunk)
            self.assertIn("section", chunk)
            self.assertIn("text", chunk)
            self.assertGreater(len(chunk["text"]), 30, "Text should be more than 30 chars")

    def test_chunks_loaded_at_startup(self):
        """Test that CHUNKS global variable is populated"""
        self.assertGreater(len(CHUNKS), 0, "CHUNKS should be loaded at module import")
        self.assertEqual(len(CHUNKS), 3, "Should have 3 chunks from data.txt")

    def test_vectorizer_and_matrix_initialized(self):
        """Test that TF-IDF vectorizer and matrix are created"""
        self.assertIsNotNone(VECTORIZER)
        self.assertIsNotNone(MATRIX)
        self.assertEqual(MATRIX.shape[0], len(CHUNKS), "Matrix rows should match chunk count")


class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_returns_ok(self):
        """Test /health endpoint returns status ok"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("chunks", data)
        self.assertGreater(data["chunks"], 0)


class TestAskEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('app.call_llm')
    def test_ask_endpoint_basic_query(self, mock_llm):
        """Test /ask endpoint with a basic regulatory query"""
        mock_llm.return_value = "Answer: Customer due diligence includes identity verification.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What is customer due diligence?",
            "top_k": 3
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("answer", data)
        self.assertIn("citations", data)
        self.assertIn("scores", data)
        self.assertIsInstance(data["citations"], list)
        self.assertIsInstance(data["scores"], list)

    @patch('app.call_llm')
    def test_ask_endpoint_with_top_k_parameter(self, mock_llm):
        """Test /ask endpoint respects top_k parameter"""
        mock_llm.return_value = "Answer: Test response.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What is enhanced due diligence?",
            "top_k": 2
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return at most top_k citations
        self.assertLessEqual(len(data["citations"]), 2)
        self.assertEqual(len(data["citations"]), len(data["scores"]))

    @patch('app.call_llm')
    def test_ask_endpoint_low_relevance_query(self, mock_llm):
        """Test /ask endpoint with irrelevant query returns NOT FOUND"""
        response = self.client.post("/ask", json={
            "question": "What is the weather today?",
            "top_k": 3
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Low similarity score should trigger NOT FOUND
        self.assertIn("NOT FOUND IN SOURCES", data["answer"])
        self.assertEqual(len(data["citations"]), 0)
        self.assertEqual(len(data["scores"]), 0)
        
        # LLM should not be called for irrelevant queries
        mock_llm.assert_not_called()

    @patch('app.call_llm')
    def test_ask_endpoint_relevant_query_calls_llm(self, mock_llm):
        """Test that relevant queries call the LLM with proper sources"""
        mock_llm.return_value = "Answer: Test.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What are customer due diligence measures?",
            "top_k": 2
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify LLM was called
        mock_llm.assert_called_once()
        
        # Check the arguments passed to call_llm
        call_args = mock_llm.call_args
        question_arg = call_args[0][0]
        sources_arg = call_args[0][1]
        
        self.assertIn("customer due diligence", question_arg.lower())
        self.assertIsInstance(sources_arg, str)
        self.assertGreater(len(sources_arg), 0)

    def test_ask_endpoint_requires_question(self):
        """Test /ask endpoint validation requires question field"""
        response = self.client.post("/ask", json={
            "top_k": 3
        })
        
        self.assertEqual(response.status_code, 422)  # Validation error

    @patch('app.call_llm')
    def test_ask_endpoint_default_top_k(self, mock_llm):
        """Test /ask endpoint uses default top_k=3 when not specified"""
        mock_llm.return_value = "Answer: Test.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What is simplified due diligence?"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should use default top_k=3
        self.assertLessEqual(len(data["citations"]), 3)

    @patch('app.call_llm')
    def test_citations_structure(self, mock_llm):
        """Test that citations have correct structure"""
        mock_llm.return_value = "Answer: Test.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What is customer due diligence?",
            "top_k": 3
        })
        
        data = response.json()
        
        for citation in data["citations"]:
            self.assertIn("doc", citation)
            self.assertIn("section", citation)
            self.assertIsInstance(citation["doc"], str)
            self.assertIsInstance(citation["section"], str)

    @patch('app.call_llm')
    def test_scores_are_floats(self, mock_llm):
        """Test that similarity scores are float values"""
        mock_llm.return_value = "Answer: Test.\nCitations: AMLD_EXCERPT (Article 13)"
        
        response = self.client.post("/ask", json={
            "question": "What is customer due diligence?",
            "top_k": 3
        })
        
        data = response.json()
        
        for score in data["scores"]:
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class TestRetrievalMechanism(unittest.TestCase):
    def test_tfidf_similarity_with_exact_match(self):
        """Test TF-IDF retrieval finds exact term matches"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Query with exact terms from Article 13
        query = "customer due diligence identity verification"
        qv = VECTORIZER.transform([query])
        sims = cosine_similarity(qv, MATRIX).flatten()
        
        # Should have non-zero similarity
        max_sim = sims.max()
        self.assertGreater(max_sim, 0.1, "Should find relevant chunks for exact terms")

    def test_tfidf_similarity_with_irrelevant_query(self):
        """Test TF-IDF retrieval returns low scores for irrelevant queries"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Completely irrelevant query
        query = "pizza recipe ingredients cooking temperature"
        qv = VECTORIZER.transform([query])
        sims = cosine_similarity(qv, MATRIX).flatten()
        
        # Should have very low or zero similarity
        max_sim = sims.max()
        self.assertLess(max_sim, 0.12, "Should have low similarity for irrelevant queries")


if __name__ == "__main__":
    unittest.main()
