# Create a protected FastAPI APIRouter for book recommendations
from fastapi import APIRouter, HTTPException, status, Depends
import google.generativeai as genai
import json
import requests
import re
import hashlib
import time
from typing import List
from app.schemas import BookQuery, Book
from app.models.user import User
from app.security import get_current_user
from app.config import settings
from app.services.gemini_service import GeminiService
# Simple in-memory cache for book recommendations
CACHE = {}
CACHE_TTL = 3600  # 1 hour cache

router = APIRouter(tags=["Book Recommendations"])


def get_cache_key(query: BookQuery) -> str:
    """Generate cache key from query parameters"""
    cache_data = {
        "query": query.query.lower().strip(),
        "count": query.count,
        "language": query.language,
        "age_group": query.age_group,
        "book_type": query.book_type,
        "content_type": query.content_type,
        "reading_level": query.reading_level,
    }
    return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()


def get_cached_books(cache_key: str) -> List[Book] | None:
    """Get books from cache if not expired"""
    if cache_key in CACHE:
        cached_data, timestamp = CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            return cached_data
        else:
            del CACHE[cache_key]  # Remove expired cache
    return None


def cache_books(cache_key: str, books: List[Book]):
    """Cache books with timestamp"""
    CACHE[cache_key] = (books, time.time())
    
    # Simple cleanup: remove old entries if cache gets too large
    if len(CACHE) > 100:
        oldest_key = min(CACHE.keys(), key=lambda k: CACHE[k][1])
        del CACHE[oldest_key]


@router.get("/filters", response_model=dict)
async def get_available_filters():
    """
    Get all available filter options for book recommendations
    """
    return {
        "languages": [
            "English", "Spanish", "French", "German", "Italian", "Portuguese", 
            "Japanese", "Chinese", "Korean", "Russian", "Arabic", "Hindi", "Bengali",
            "Tamil", "Telugu", "Marathi", "Gujarati", "Urdu", "Punjabi", "Sanskrit"
        ],
        "target_audiences": [
            {"value": "children", "description": "Ages 4-12, fun and educational stories"},
            {"value": "young_adult", "description": "Ages 13-18, coming-of-age themes"},
            {"value": "adult", "description": "Mature themes, complex narratives"},
            {"value": "general", "description": "Suitable for all ages"}
        ],
        "book_types": [
            {"value": "fiction", "description": "Novels, stories, imaginative narratives"},
            {"value": "non_fiction", "description": "Factual, biographical, informational"},
            {"value": "biography", "description": "Life stories of real people"},
            {"value": "memoir", "description": "Personal life experiences and memories"},
            {"value": "textbook", "description": "Educational, academic, learning-focused"},
            {"value": "reference", "description": "Dictionaries, encyclopedias, guides"}
        ],
        "content_types": [
            {"value": "novel", "description": "Full-length fictional narrative"},
            {"value": "short_stories", "description": "Collection of short fictional works"},
            {"value": "poetry", "description": "Poetic works and verse collections"},
            {"value": "essays", "description": "Non-fiction essay collections"},
            {"value": "academic", "description": "Scholarly, research-based content"},
            {"value": "self_help", "description": "Personal development and motivation"}
        ],
        "reading_levels": [
            {"value": "beginner", "description": "Simple language, easy concepts"},
            {"value": "intermediate", "description": "Moderate complexity, accessible"},
            {"value": "advanced", "description": "Complex themes, sophisticated writing"},
            {"value": "expert", "description": "Highly specialized, academic level"}
        ]
    }

# Configure the Google Gemini API client
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')


def get_book_cover_url(title: str, author: str, isbn: str = None) -> str:
    """
    Get book cover URL from multiple sources
    """
    # Try Open Library first if we have ISBN
    if isbn and isbn.strip():
        # Clean ISBN (remove dashes and spaces)
        clean_isbn = re.sub(r'[-\s]', '', isbn.strip())
        openlibrary_url = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg"
        
        # Check if the URL is valid
        try:
            response = requests.head(openlibrary_url, timeout=3)
            if response.status_code == 200:
                return openlibrary_url
        except:
            pass
    
    # Try Google Books API search
    try:
        search_query = f"{title} {author}".replace(" ", "+")
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}&maxResults=1"
        response = requests.get(google_books_url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                volume_info = data['items'][0].get('volumeInfo', {})
                image_links = volume_info.get('imageLinks', {})
                
                # Try different image sizes
                for size in ['large', 'medium', 'small', 'thumbnail']:
                    if size in image_links:
                        # Convert HTTP to HTTPS for security
                        img_url = image_links[size].replace('http://', 'https://')
                        return img_url
    except:
        pass
    
    # Fallback to a simple data URI placeholder
    return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjQ1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzRBNTU2OCIvPgo8dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSIjRkZGRkZGIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Qm9vayBDb3ZlcjwvdGV4dD4KPC9zdmc+"


# Quick recommendations endpoint for fast initial results
@router.post("/quick", response_model=List[Book])
async def get_quick_recommendations(
    query: BookQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Get quick book recommendations (5 books max) for fast initial display  
    """
    # Force quick mode - max 5 books
    query.count = 5
    query.get_all_available = False
    
    # Check cache first
    cache_key = f"quick_{get_cache_key(query)}"
    cached_books = get_cached_books(cache_key)
    if cached_books:
        return cached_books
    
    # Use minimal prompt for speed
    filter_summary = f"Lang: {query.language or 'Any'}, Type: {query.book_type or 'Any'}"
    
    prompt = f"""Quick book recommendations for: "{query.query}"
    Filters: {filter_summary}
    
    Return ONLY this JSON (5 books max):
    {{
      "books": [
        {{
          "title": "Title",
          "author": "Author", 
          "genre": "Genre",
          "brief_summary": "Brief plot",
          "short_description": "Why recommended",
          "isbn": null,
          "publication_year": 2020,
          "rating": 4.0,
          "language": "English",
          "age_group": "{query.age_group or 'adult'}",
          "target_audience": "{query.target_audience or 'general'}",
          "book_type": "{query.book_type or 'fiction'}",
          "content_type": "{query.content_type or 'entertainment'}",
          "reading_level": "{query.reading_level or 'intermediate'}",
          "page_count": 300,
          "series_info": null
        }}
      ]
    }}"""
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Quick cleanup
        if "```" in response_text:
            response_text = response_text.split("```")[1] if response_text.count("```") >= 2 else response_text.replace("```", "")
        
        json_response = json.loads(response_text.strip())
        
        # Fast book processing
        books = []
        for book_data in json_response.get("books", [])[:5]:  # Ensure max 5
            if book_data.get("isbn"):
                clean_isbn = re.sub(r'[-\\s]', '', book_data["isbn"].strip())
                book_data["cover_image_url"] = f"https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg"
            else:
                # Use data URI for immediate loading without network request
                book_data["cover_image_url"] = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjQ1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzRBNTU2OCIvPgo8dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE4IiBmaWxsPSIjRkZGRkZGIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+Tm8gQ292ZXI8L3RleHQ+CjwvcNZn4="
            
            books.append(Book(**book_data))
        
        # Cache the results
        cache_books(cache_key, books)
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick recommendation error: {str(e)}"
        )

# Enhanced recommendations endpoint using GeminiService
@router.post("/", response_model=List[Book])
async def get_book_recommendations(
    query: BookQuery,
    current_user: User = Depends(get_current_user)
):
    """Get book recommendations using enhanced GeminiService with proper filtering"""
    try:
        print(f"🔍 Processing recommendation request:")
        print(f"   Query: {query.query}")
        print(f"   Count requested: {query.count} books")
        print(f"   Language: {query.language}")
        print(f"   Age Group: {query.age_group}")
        print(f"   Book Type: {query.book_type}")
        print(f"   Content Type: {query.content_type}")
        print(f"   Reading Level: {query.reading_level}")
        print(f"   🎯 MUST RETURN EXACTLY {query.count} BOOKS")
        
        # Build enhanced query string with filters
        enhanced_query = query.query
        filters = []
        
        if query.language and query.language != "none":
            filters.append(f"in {query.language} language")
        if query.age_group and query.age_group != "none":
            filters.append(f"for {query.age_group} audience")
        if query.book_type and query.book_type != "none":
            filters.append(f"{query.book_type} books")
        if query.content_type and query.content_type != "none":
            filters.append(f"{query.content_type} format")
        if query.reading_level and query.reading_level != "none":
            filters.append(f"{query.reading_level} reading level")
        
        if filters:
            enhanced_query += f" (specifically: {', '.join(filters)})"
        
        print(f"📝 Enhanced query: {enhanced_query}")
        
        # Check cache first
        cache_key = get_cache_key(query)
        cached_books = get_cached_books(cache_key)
        if cached_books:
            print(f"🎯 Returning {len(cached_books)} books from cache")
            return cached_books
        
        # Use GeminiService for recommendations
        requested_count = query.count if query.count and query.count > 0 else 20
        print(f"📊 Requesting {requested_count} recommendations from Gemini")
        
        recommendation_response = await GeminiService.generate_recommendations(
            user_query=enhanced_query,
            max_recommendations=requested_count
        )
        
        books = recommendation_response.recommendations
        print(f"✅ Generated {len(books)} recommendations using GeminiService")
        
        # Cache the results
        cache_books(cache_key, books)
        
        return books
        
    except HTTPException:
        # Re-raise HTTPExceptions from GeminiService
        raise
    except Exception as e:
        print(f"❌ Recommendation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )