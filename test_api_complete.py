import requests
import json

# Test the book recommendations API
def test_api():
    # First, we need to create a user and get a token
    base_url = "http://localhost:8000"
    
    # Create a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    print("Testing Book Recommendations API with Filters")
    print("=" * 50)
    
    try:
        # Register user
        print("1. Registering test user...")
        register_response = requests.post(f"{base_url}/auth/register", json=user_data)
        
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        elif register_response.status_code == 409:
            print("✅ User already exists, proceeding with login")
        else:
            print(f"❌ Registration failed: {register_response.text}")
            return
        
        # Login to get token
        print("2. Logging in...")
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = requests.post(f"{base_url}/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print("✅ Login successful")
        
        # Test book recommendations with different filter-focused queries
        headers = {"Authorization": f"Bearer {access_token}"}
        
        test_queries = [
            "Hindi fiction novels for adults",
            "English children's adventure books", 
            "French mystery novels for intermediate readers",
            "Non-fiction self-help books in English for adults"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing query: '{query}'")
            print("-" * 40)
            
            book_request = {
                "query": query,
                "max_recommendations": 3
            }
            
            response = requests.post(
                f"{base_url}/books/recommendations", 
                json=book_request, 
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                books = data["recommendations"]
                print(f"✅ Generated {len(books)} books")
                
                for j, book in enumerate(books, 1):
                    print(f"\n  Book {j}: {book['title']} by {book['author']}")
                    print(f"    Language: {book.get('language', 'N/A')}")
                    print(f"    Target Audience: {book.get('target_audience', 'N/A')}")
                    print(f"    Book Type: {book.get('book_type', 'N/A')}")
                    print(f"    Content Type: {book.get('content_type', 'N/A')}")
                    print(f"    Reading Level: {book.get('reading_level', 'N/A')}")
                    
                    # Check if all filter fields are present
                    filter_fields = ['language', 'target_audience', 'book_type', 'content_type', 'reading_level']
                    missing = [field for field in filter_fields if not book.get(field)]
                    
                    if missing:
                        print(f"    ⚠️  Missing fields: {', '.join(missing)}")
                    else:
                        print(f"    ✅ All filter fields present")
            else:
                print(f"❌ Request failed: {response.status_code} - {response.text}")
        
        # Test filters endpoint
        print(f"\n5. Testing available filters endpoint")
        print("-" * 40)
        filters_response = requests.get(f"{base_url}/recommendations/filters")
        
        if filters_response.status_code == 200:
            filters = filters_response.json()
            print("✅ Available filters:")
            print(f"  Languages: {len(filters['languages'])} options")
            print(f"  Target Audiences: {len(filters['target_audiences'])} options")
            print(f"  Book Types: {len(filters['book_types'])} options")
            print(f"  Content Types: {len(filters['content_types'])} options")
            print(f"  Reading Levels: {len(filters['reading_levels'])} options")
        else:
            print(f"❌ Filters request failed: {filters_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    test_api()