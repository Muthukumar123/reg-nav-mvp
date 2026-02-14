#!/usr/bin/env python3
"""
Demo script to showcase logging and exception handling in the Regulation Navigator.
"""
import logging
import sys
from fastapi.testclient import TestClient

# Configure logging to show INFO and above
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app import app

def main():
    print("=" * 70)
    print("Regulation Navigator - Logging & Exception Handling Demo")
    print("=" * 70)
    
    client = TestClient(app)
    
    # Test 1: Health check (normal operation)
    print("\n1. Testing Health Endpoint (Normal Operation)")
    print("-" * 70)
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Valid question (normal operation with LLM call)
    print("\n2. Testing Valid Question (Mocked LLM)")
    print("-" * 70)
    from unittest.mock import patch
    with patch('app.call_llm') as mock_llm:
        mock_llm.return_value = "Answer: Customer due diligence includes verifying identity.\\nCitations: AMLD_EXCERPT (Article 13)"
        response = client.post("/ask", json={
            "question": "What is customer due diligence?",
            "top_k": 2
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    
    # Test 3: Irrelevant question (low similarity, no LLM call)
    print("\n3. Testing Irrelevant Question (Below Threshold)")
    print("-" * 70)
    response = client.post("/ask", json={
        "question": "What is the capital of France?",
        "top_k": 3
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: Invalid request (validation error)
    print("\n4. Testing Invalid Request (Missing Question)")
    print("-" * 70)
    response = client.post("/ask", json={
        "top_k": 3
    })
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 5: LLM failure simulation
    print("\n5. Testing LLM Failure (Simulated)")
    print("-" * 70)
    with patch('app.call_llm') as mock_llm:
        mock_llm.side_effect = Exception("Azure OpenAI service unavailable")
        response = client.post("/ask", json={
            "question": "What is enhanced due diligence?",
            "top_k": 2
        })
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()
