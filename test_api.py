#!/usr/bin/env python3
"""
Test script for the Recipe Extraction API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

def test_api():
    """Test the FastAPI endpoints"""
    client = TestClient(app)
    
    print("Testing Recipe Extraction API...")
    print("=" * 50)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test root endpoint
    print("2. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print()
    
    # Test OpenAPI docs
    print("3. Testing OpenAPI docs...")
    response = client.get("/openapi.json")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        openapi_data = response.json()
        print(f"   API Title: {openapi_data.get('info', {}).get('title')}")
        print(f"   Version: {openapi_data.get('info', {}).get('version')}")
        print(f"   Endpoints: {len(openapi_data.get('paths', {}))}")
    print()
    
    # Test recipe extraction endpoint (with invalid URL to test validation)
    print("4. Testing recipe extraction endpoint validation...")
    try:
        response = client.post("/extract", json={
            "video_url": "invalid-url",
            "max_retries": 2
        })
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Error response: {response.json()}")
    except Exception as e:
        print(f"   Validation error (expected): {e}")
    print()
    
    print("✅ API tests completed!")

if __name__ == "__main__":
    test_api()