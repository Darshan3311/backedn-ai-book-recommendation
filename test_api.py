#!/usr/bin/env python3
"""
Test script for the Book Recommendations API
Tests all endpoints to ensure complete functionality
"""

import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

async def test_api():
    """Test all API endpoints"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Book Recommendations API\n")
        
        # Test 1: Root endpoint
        print("1. Testing root endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            assert response.status_code == 200
            print("   ✅ Root endpoint working\n")
        except Exception as e:
            print(f"   ❌ Root endpoint failed: {e}\n")
            return
        
        # Test 2: Health check
        print("2. Testing health endpoint...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            assert response.status_code == 200
            print("   ✅ Health endpoint working\n")
        except Exception as e:
            print(f"   ❌ Health endpoint failed: {e}\n")
        
        # Test 3: User registration
        print("3. Testing user registration...")
        test_user = {
            "username": "testuser",
            "password": "testpassword123"
        }
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=test_user)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
            if response.status_code == 201:
                print("   ✅ User registration working\n")
            elif response.status_code == 400 and "already registered" in response.json().get("detail", ""):
                print("   ✅ User already exists (expected for repeated tests)\n")
            else:
                print("   ❌ Unexpected registration response\n")
        except Exception as e:
            print(f"   ❌ User registration failed: {e}\n")
        
        # Test 4: User login
        print("4. Testing user login...")
        login_data = {
            "username": test_user["username"],
            "password": test_user["password"]
        }
        try:
            response = await client.post(
                f"{BASE_URL}/auth/login",
                data=login_data,  # OAuth2PasswordRequestForm expects form data
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                print(f"   Token received: {access_token[:20]}...")
                print("   ✅ User login working\n")
                
                # Test 5: Protected endpoint (book recommendations)
                print("5. Testing book recommendations (protected endpoint)...")
                headers = {"Authorization": f"Bearer {access_token}"}
                recommendation_query = {"query": "psychological thrillers with twist endings"}
                
                try:
                    response = await client.post(
                        f"{BASE_URL}/recommendations/",
                        json=recommendation_query,
                        headers=headers
                    )
                    print(f"   Status: {response.status_code}")
                    if response.status_code == 200:
                        books = response.json()
                        print(f"   Received {len(books)} book recommendations:")
                        for i, book in enumerate(books[:2], 1):  # Show first 2 books
                            print(f"     {i}. {book['title']} by {book['author']}")
                            print(f"        Genre: {book['genre']}")
                            print(f"        Summary: {book['brief_summary'][:100]}...")
                        print("   ✅ Book recommendations working\n")
                    else:
                        print(f"   ❌ Book recommendations failed: {response.json()}\n")
                except Exception as e:
                    print(f"   ❌ Book recommendations failed: {e}\n")
                    
            else:
                print(f"   ❌ Login failed: {response.json()}\n")
        except Exception as e:
            print(f"   ❌ User login failed: {e}\n")
        
        # Test 6: API Documentation
        print("6. Testing API documentation...")
        try:
            response = await client.get(f"{BASE_URL}/docs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ API documentation accessible\n")
            else:
                print("   ❌ API documentation not accessible\n")
        except Exception as e:
            print(f"   ❌ API documentation failed: {e}\n")
        
        print("🎉 API testing completed!")
        print(f"📖 API Documentation: {BASE_URL}/docs")
        print(f"🔄 Alternative Docs: {BASE_URL}/redoc")

if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:8000")
    print("Start server with: python run.py")
    print("=" * 50)
    asyncio.run(test_api())