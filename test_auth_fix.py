"""
Simple script to test the authentication fix
"""
import requests
import json

def test_auth_flow():
    """Test the complete authentication and book recommendation flow"""
    base_url = "http://localhost:8000"
    
    print("Testing Authentication Flow Fix")
    print("=" * 40)
    
    # Test user credentials
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        # 1. Register user (if needed)
        print("1. Attempting user registration...")
        register_response = requests.post(f"{base_url}/auth/register", json=user_data)
        
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        elif register_response.status_code == 409:
            print("✅ User already exists, proceeding with login")
        else:
            print(f"❌ Registration failed: {register_response.status_code} - {register_response.text}")
            return
        
        # 2. Login to get token
        print("\n2. Logging in...")
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = requests.post(
            f"{base_url}/auth/login", 
            data=login_data,  # Use data for form-encoded
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print("✅ Login successful, token received")
        print(f"   Token type: {token_data.get('token_type', 'N/A')}")
        print(f"   Token preview: {access_token[:20]}...")
        
        # 3. Test the /auth/me endpoint to verify token works
        print("\n3. Testing token validation...")
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{base_url}/auth/me", headers=headers)
        
        if me_response.status_code == 200:
            user_info = me_response.json()
            print("✅ Token validation successful")
            print(f"   User: {user_info.get('username')} ({user_info.get('email')})")
        else:
            print(f"❌ Token validation failed: {me_response.status_code} - {me_response.text}")
            return
        
        # 4. Test the book recommendations endpoint (the one that was failing)
        print("\n4. Testing book recommendations endpoint...")
        book_request = {
            "query": "science fiction novels for adults",
            "max_recommendations": 2
        }
        
        book_response = requests.post(
            f"{base_url}/books/recommendations",
            json=book_request,
            headers=headers
        )
        
        if book_response.status_code == 200:
            data = book_response.json()
            books = data.get("recommendations", [])
            print(f"✅ Book recommendations successful! Got {len(books)} books")
            
            for i, book in enumerate(books, 1):
                print(f"   Book {i}: {book.get('title', 'N/A')} by {book.get('author', 'N/A')}")
                print(f"      Language: {book.get('language', 'N/A')}")
                print(f"      Target Audience: {book.get('target_audience', 'N/A')}")
        else:
            print(f"❌ Book recommendations failed: {book_response.status_code} - {book_response.text}")
            if book_response.status_code == 401:
                print("   This indicates an authentication issue!")
            return
        
        print("\n" + "=" * 40)
        print("🎉 ALL TESTS PASSED! Authentication fix is working!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    print("Make sure the backend server is running on http://localhost:8000")
    print("Run: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    test_auth_flow()