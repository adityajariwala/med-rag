#!/usr/bin/env python
"""
Simple script to test the Med-RAG API
Usage: python scripts/test_api.py
"""

import requests
import json
import sys

API_URL = "http://localhost:8000"


def test_health():
    """Test the health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200


def test_query(question: str):
    """Test the query endpoint"""
    print(f"Testing /query endpoint with question: '{question}'")
    payload = {"question": question}

    response = requests.post(f"{API_URL}/query", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nAnswer Summary:")
        print(result["answer"]["answer_summary"])
        print(f"\nConfidence: {result['answer']['confidence']}")
        print(f"\nEvidence Count: {len(result['answer']['evidence'])}")
        print(f"\nMetrics:")
        print(json.dumps(result["metrics"], indent=2))
    else:
        print(f"Error: {response.text}")

    return response.status_code == 200


def main():
    """Run API tests"""
    print("=" * 60)
    print("Med-RAG API Test Suite")
    print("=" * 60 + "\n")

    # Test health endpoint
    if not test_health():
        print("❌ Health check failed. Is the API running?")
        print("Start it with: uvicorn src.api:app --reload")
        sys.exit(1)

    print("✅ Health check passed\n")

    # Test query endpoint
    test_questions = [
        "What evidence exists linking GLP-1 agonists to cardiovascular outcomes?",
        "What are the side effects of GLP-1 agonists?",
    ]

    for question in test_questions:
        print("-" * 60)
        if test_query(question):
            print("✅ Query succeeded\n")
        else:
            print("❌ Query failed\n")

    print("=" * 60)
    print("Tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
