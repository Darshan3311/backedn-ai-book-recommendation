"""
Test script to debug book generation and filtering issues
"""
import asyncio
import json
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.gemini_service import GeminiService
from app.config import settings


async def test_book_generation():
    """Test Gemini book generation with different queries and filter contexts"""
    
    print("Testing Gemini Book Generation and Filtering")
    print("=" * 50)
    
    # Test queries with specific filter requirements
    test_queries = [
        "Hindi fiction novels for adults",
        "English children's books about adventure", 
        "Spanish romance novels for young adults",
        "Non-fiction self-help books in English",
        "Japanese poetry books for advanced readers",
        "French mystery novels for intermediate readers"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing query: '{query}'")
        print("-" * 40)
        
        try:
            # Generate recommendations
            response = await GeminiService.generate_recommendations(query, max_recommendations=3)
            
            print(f"✅ Generated {len(response.recommendations)} books")
            
            # Analyze each book for filter metadata
            for j, book in enumerate(response.recommendations, 1):
                print(f"\n  Book {j}: {book.title} by {book.author}")
                print(f"    Language: {book.language}")
                print(f"    Target Audience: {book.target_audience}")
                print(f"    Book Type: {book.book_type}")
                print(f"    Content Type: {book.content_type}")
                print(f"    Reading Level: {book.reading_level}")
                print(f"    Genre: {book.genre}")
                
                # Check if filter fields are properly populated
                missing_fields = []
                if not book.language:
                    missing_fields.append("language")
                if not book.target_audience:
                    missing_fields.append("target_audience")
                if not book.book_type:
                    missing_fields.append("book_type")
                if not book.content_type:
                    missing_fields.append("content_type")
                if not book.reading_level:
                    missing_fields.append("reading_level")
                
                if missing_fields:
                    print(f"    ⚠️  Missing filter fields: {', '.join(missing_fields)}")
                else:
                    print(f"    ✅ All filter fields populated")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Test completed!")


async def test_specific_filters():
    """Test how filtering works with specific filter values"""
    print("\n\nTesting Filter Logic")
    print("=" * 50)
    
    # Generate some books first
    query = "recommend me various books in different languages and genres"
    response = await GeminiService.generate_recommendations(query, max_recommendations=10)
    
    books = response.recommendations
    print(f"Generated {len(books)} books for filtering test")
    
    # Test different filter combinations
    filter_tests = [
        {"language": "English"},
        {"target_audience": "adult"},
        {"book_type": "fiction"},
        {"content_type": "novel"},
        {"reading_level": "intermediate"},
        {"language": "Hindi", "target_audience": "adult"},
        {"book_type": "non_fiction", "reading_level": "beginner"}
    ]
    
    for filter_combo in filter_tests:
        print(f"\nTesting filter: {filter_combo}")
        
        # Apply filters manually (same logic as frontend)
        filtered_books = []
        for book in books:
            matches = True
            
            for key, value in filter_combo.items():
                book_value = getattr(book, key, None)
                if book_value != value:
                    matches = False
                    break
            
            if matches:
                filtered_books.append(book)
        
        print(f"  Found {len(filtered_books)} matching books:")
        for book in filtered_books:
            print(f"    - {book.title} ({book.language}, {book.target_audience}, {book.book_type})")
        
        if not filtered_books:
            print("  ❌ No books found! This might be the issue.")
            # Show what values are actually available
            print("  Available values in dataset:")
            for field in filter_combo.keys():
                values = set(getattr(book, field, None) for book in books if getattr(book, field, None))
                print(f"    {field}: {list(values)}")


async def main():
    """Main test function"""
    if not settings.gemini_api_key:
        print("❌ Gemini API key not found! Please set GEMINI_API_KEY environment variable.")
        return
    
    print(f"✅ Gemini API key configured")
    
    # Test connection first
    try:
        is_connected = await GeminiService.test_gemini_connection()
        if is_connected:
            print("✅ Gemini connection successful")
        else:
            print("❌ Gemini connection failed")
            return
    except Exception as e:
        print(f"❌ Gemini connection error: {str(e)}")
        return
    
    # Run tests
    await test_book_generation()
    await test_specific_filters()


if __name__ == "__main__":
    asyncio.run(main())