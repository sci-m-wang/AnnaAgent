#!/usr/bin/env python3
"""
Simple test script for AnnaAgent FastAPI server.
Tests both the simple chat endpoint and session-based endpoints.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8080"

def test_simple_chat():
    """Test the simple chat endpoint."""
    print("=== Testing Simple Chat Endpoint ===")
    
    endpoint = f"{API_BASE_URL}/api/chat/simple"
    test_message = "你好，最近心情怎么样？"
    
    payload = {"message": test_message}
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"Request: {test_message}")
        print(f"Response: {result['response']}")
        print(f"Timestamp: {result['timestamp']}")
        print("✅ Simple chat test passed!\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple chat test failed: {str(e)}\n")
        return False

def test_session_workflow():
    """Test the complete session workflow."""
    print("=== Testing Session Workflow ===")
    
    # 1. Create session
    create_endpoint = f"{API_BASE_URL}/api/sessions"
    profile_data = {
        "profile": {
            "age": "25",
            "gender": "女",
            "occupation": "大学生",
            "martial_status": "未婚",
            "symptoms": "学业焦虑，对未来迷茫"
        },
        "report": {
            "title": "大学生学业焦虑咨询"
        }
    }
    
    try:
        # Create session
        print("1. Creating session...")
        response = requests.post(create_endpoint, json=profile_data, timeout=30)
        response.raise_for_status()
        
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ Session created: {session_id}")
        
        # 2. Send multiple messages
        chat_endpoint = f"{API_BASE_URL}/api/sessions/{session_id}/chat"
        
        test_messages = [
            "你好，医生",
            "我最近很担心找不到工作",
            "你能给我一些建议吗？"
        ]
        
        print("\n2. Testing conversation...")
        for i, message in enumerate(test_messages, 1):
            print(f"\nMessage {i}: {message}")
            
            response = requests.post(chat_endpoint, json={"message": message}, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"Patient: {result['response']}")
            print(f"Message count: {result['message_count']}")
            if result.get('complaint_stage'):
                print(f"Complaint stage: {result['complaint_stage']}")
            
            time.sleep(1)  # Brief pause between messages
        
        # 3. Get session details
        print("\n3. Getting session details...")
        details_endpoint = f"{API_BASE_URL}/api/sessions/{session_id}"
        response = requests.get(details_endpoint, timeout=30)
        response.raise_for_status()
        
        details = response.json()
        print(f"Total messages: {details['metadata']['message_count']}")
        print(f"Conversation history length: {len(details['conversation'])}")
        
        print("\n✅ Session workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Session workflow test failed: {str(e)}")
        return False

def test_api_health():
    """Test health check endpoint."""
    print("=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        
        result = response.json()
        print(f"Status: {result['status']}")
        print("✅ Health check passed!\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}\n")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting AnnaAgent API Tests...\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        print(f"Server info: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ Cannot connect to server at {API_BASE_URL}")
        print("Make sure the server is running with: python api_server.py")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_api_health),
        ("Simple Chat", test_simple_chat),
        ("Session Workflow", test_session_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print("-" * 50)
    
    # Summary
    print("\n📊 Test Results Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()