"""
Test script to verify filter functionality end-to-end
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.gemini_service import GeminiService
from app.config import settings


async def test_filter_generation():
    """Test that AI generates proper filter metadata"""
    
    print("Testing Filter Generation and Validation")
    print("=" * 50)
    
    # Test queries designed to trigger specific filters
    test_cases = [
        {
            "query": "Hindi fiction novels for adults",
            "expected": {
                "language": "Hindi",
                "target_audience": "adult", 
                "book_type": "fiction",
                "content_type": "novel"
            }
        },
        {
            "query": "English children's adventure books",
            "expected": {
                "language": "English",
                "target_audience": "children",
                "book_type": "fiction"
            }
        },
        {
            "query": "Non-fiction self-help books for beginners",
            "expected": {
                "book_type": "non_fiction",
                "content_type": "self_help",
                "reading_level": "beginner"
            }
        },
        {
            "query": "Spanish poetry collections for advanced readers",
            "expected": {
                "language": "Spanish",
                "content_type": "poetry",
                "reading_level": "advanced"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{test_case['query']}'")
        print("-" * 40)
        
        try:
            response = await GeminiService.generate_recommendations(
                test_case["query"], 
                max_recommendations=3
            )
            
            books = response.recommendations
            print(f"✅ Generated {len(books)} books")
            
            # Check each book's filter metadata
            for j, book in enumerate(books, 1):
                print(f"\n  Book {j}: {book.title}")
                print(f"    Author: {book.author}")
                
                # Check filter fields
                filter_check = {
                    "language": book.language,
                    "target_audience": book.target_audience,
                    "book_type": book.book_type,
                    "content_type": book.content_type,
                    "reading_level": book.reading_level
                }
                
                print("    Filter Values:")
                for field, value in filter_check.items():
                    expected = test_case["expected"].get(field)
                    if expected:
                        status = "✅" if value == expected else "❌"
                        print(f"      {field}: {value} {status} (expected: {expected})")
                    else:
                        print(f"      {field}: {value}")
                
                # Check for missing values
                missing_fields = [field for field, value in filter_check.items() if not value]
                if missing_fields:
                    print(f"    ⚠️  Missing fields: {', '.join(missing_fields)}")
                else:
                    print(f"    ✅ All filter fields populated")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Filter generation test completed!")


async def test_filter_validation():
    """Test the filter validation and normalization function"""
    
    print("\n\nTesting Filter Validation")
    print("=" * 30)
    
    # Test cases with invalid/inconsistent data
    test_data_cases = [
        {
            "input": {
                "title": "Test Book",
                "author": "Test Author",
                "language": "english",  # lowercase
                "target_audience": "Adult",  # capitalized
                "book_type": "non-fiction",  # hyphenated
                "content_type": "Self Help",  # spaced
                "reading_level": "INTERMEDIATE"  # all caps
            },
            "expected": {
                "language": "English",
                "target_audience": "adult",
                "book_type": "non_fiction",
                "content_type": "self_help",
                "reading_level": "intermediate"
            }
        },
        {
            "input": {
                "title": "Test Book 2",
                "author": "Test Author 2",
                "language": "invalid_language",
                "target_audience": "invalid_audience",
                "book_type": "invalid_type",
                "content_type": "invalid_content",
                "reading_level": "invalid_level"
            },
            "expected": {
                "language": "English",  # default
                "target_audience": "general",  # default
                "book_type": "fiction",  # default
                "content_type": "novel",  # default
                "reading_level": "intermediate"  # default
            }
        }
    ]
    
    for i, test_case in enumerate(test_data_cases, 1):
        print(f"\n{i}. Testing validation:")
        print(f"   Input: {test_case['input']}")
        
        normalized = GeminiService.validate_and_normalize_filters(test_case["input"].copy())
        
        print(f"   Output: language={normalized['language']}, target_audience={normalized['target_audience']}")
        print(f"           book_type={normalized['book_type']}, content_type={normalized['content_type']}")
        print(f"           reading_level={normalized['reading_level']}")
        
        # Check if normalization worked as expected
        all_correct = True
        for field, expected_value in test_case["expected"].items():
            actual_value = normalized.get(field)
            if actual_value != expected_value:
                print(f"   ❌ {field}: expected '{expected_value}', got '{actual_value}'")
                all_correct = False
        
        if all_correct:
            print(f"   ✅ All fields normalized correctly")
    
    print("\n" + "=" * 30)
    print("Filter validation test completed!")


async def main():
    """Main test function"""
    if not settings.gemini_api_key:
        print("❌ Gemini API key not found! Please set GEMINI_API_KEY environment variable.")
        return
    
    print("🔍 Testing Filter System Functionality")
    print("📋 This will test both AI generation and validation")
    print()
    
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
    await test_filter_validation()
    await test_filter_generation()


if __name__ == "__main__":
    asyncio.run(main())