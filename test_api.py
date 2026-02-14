#!/usr/bin/env python3
"""
Quick API Test Script - Demonstrates all endpoints
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("REGULATION NAVIGATOR API - LIVE TEST")
print("=" * 70)

# Test 1: Root endpoint
print("\n1️⃣  Testing Root Endpoint: GET /")
print("-" * 70)
response = requests.get(f"{BASE_URL}/")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 2: Health check
print("\n2️⃣  Testing Health Endpoint: GET /health")
print("-" * 70)
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Test 3: Ask endpoint with a real question
print("\n3️⃣  Testing Ask Endpoint: POST /ask")
print("-" * 70)
question = "What is customer due diligence?"
print(f"Question: {question}")
print("Sending request to LLM...")

try:
    response = requests.post(
        f"{BASE_URL}/ask",
        json={"question": question, "top_k": 2},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nCitations: {result['citations']}")
        print(f"Similarity Scores: {result['scores']}")
    else:
        print(f"Error: {response.json()}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 4: Irrelevant question
print("\n4️⃣  Testing with Irrelevant Question")
print("-" * 70)
question = "What is the weather today?"
print(f"Question: {question}")

response = requests.post(
    f"{BASE_URL}/ask",
    json={"question": question, "top_k": 2}
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Answer: {result['answer']}")

print("\n" + "=" * 70)
print("✅ API TEST COMPLETE!")
print("=" * 70)
print(f"\n📚 Access Swagger UI at: {BASE_URL}/docs")
print(f"📖 Access ReDoc at: {BASE_URL}/redoc")
print("=" * 70)
