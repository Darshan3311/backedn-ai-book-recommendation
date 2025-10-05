import json
import re
import aiohttp
import urllib.parse
from typing import List, Optional, Dict, Set
from datetime import datetime
import google.generativeai as genai
from fastapi import HTTPException, status
from app.models.book import Book, BookRecommendationResponse
from app.config import settings

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)

# REFINEMENT: Moved genre keywords to a class-level constant for reusability
# This dictionary maps genres to keywords for cleaner detection logic.
# More specific, multi-word genres are placed first to ensure correct matching.
GENRE_KEYWORDS = {
    "Historical Biography": ["historical biography", "freedom", "independence"],
    "Historical Fiction": ["historical fiction"],
    "Science Fiction": ["science fiction", "sci-fi"],
    "True Crime": ["true crime"],
    "Young Adult (YA)": ["young adult", "ya"],
    "Graphic Novel": ["graphic novel", "comic book"],
    "Self-Help": ["self-help", "self improvement", "motivation"],
    "Cookbook": ["cookbook", "recipe"],
    "Business/Economics": ["business", "economics", "finance"],
    "Children's Literature": ["children's", "kids", "picture book"],
    "Horror": ["horror", "scary", "chilling"],
    "Romance": ["romance", "love story"],
    "Mystery": ["mystery", "detective"],
    "Crime Fiction": ["crime"],
    "Thriller/Suspense": ["thriller", "suspense"],
    "Biography/Memoir": ["biography", "memoir"],
    "History": ["history", "historical"],
    "Fantasy": ["fantasy", "magic", "dragon"],
    "Dystopian": ["dystopian", "apocalyptic"],
    "Adventure": ["adventure", "quest", "journey"],
    "Comedy/Humor": ["comedy", "humor", "funny"],
    "Philosophy": ["philosophy"],
    "Science (Non-Fiction)": ["science"],
    "Classic": ["classic", "literature"],
    "Travel": ["travel", "guidebook"],
}


class GeminiService:
    """Service for generating book recommendations using Google Gemini API"""

    @staticmethod
    async def fetch_book_cover(title: str, author: str) -> Optional[str]:
        """Fetch real book cover from Google Books API with multiple search strategies"""
        try:
            search_queries = [
                f'intitle:"{title}" inauthor:"{author}"',
                f'{title} {author}',
                f'intitle:{title.split()[0]} inauthor:{author.split()[0]}' if ' ' in title and ' ' in author else None,
                title
            ]
            search_queries = [q for q in search_queries if q]

            for query in search_queries:
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=3"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('totalItems', 0) > 0:
                                for item in data.get('items', [])[:3]:
                                    volume_info = item.get('volumeInfo', {})
                                    image_links = volume_info.get('imageLinks', {})
                                    for size in ['extraLarge', 'large', 'medium', 'small', 'thumbnail']:
                                        if size in image_links:
                                            cover_url = image_links[size]
                                            cover_url = cover_url.replace('http:', 'https:')
                                            cover_url = cover_url.replace('&edge=curl', '')
                                            cover_url = cover_url.replace('zoom=1', 'zoom=0')
                                            return cover_url
        except Exception as e:
            print(f"Error fetching cover for '{title}' by '{author}': {str(e)}")
        
        return None

    @staticmethod
    def generate_fallback_cover(title: str, author: str) -> str:
        """Generate a stylish fallback cover image"""
        try:
            colors = [
                "667eea", "764ba2", "f093fb", "f5576c", "4facfe", "43e97b", 
                "38ef7d", "eea2a2", "bbc1c1", "57c6e1", "b721ff", "21d4fd"
            ]
            color_index = hash(title.lower()) % len(colors)
            bg_color = colors[color_index]
            
            title_clean = urllib.parse.quote(title[:20])
            author_clean = urllib.parse.quote(author[:15])
            
            return f"https://via.placeholder.com/300x400/{bg_color}/ffffff.png?text={title_clean}%0A%0A{author_clean}"
        except Exception as e:
            print(f"Error generating fallback cover: {str(e)}")
            return "https://via.placeholder.com/300x400/4A5568/ffffff.png?text=Book+Cover"

    @staticmethod
    def create_enhanced_prompt(user_query: str, max_recommendations: int) -> str:
        """Create a strict prompt for Gemini to generate precisely matching book recommendations"""
        return f"""You are a PRECISION book recommendation system. Your ONLY job is to find books that EXACTLY match the user's request.

USER QUERY: "{user_query}"
REQUIRED OUTPUT: EXACTLY {max_recommendations} books - NO MORE, NO LESS.

🚨 CRITICAL QUANTITY REQUIREMENT: 
- You MUST return exactly {max_recommendations} books.
- If you find fewer than {max_recommendations} perfect matches, expand your search but maintain quality.
- Count your books before responding.

ULTRA-STRICT MATCHING RULES:
- If a GENRE is mentioned (horror, romance, etc.), ALL books must be that genre.
- If a LANGUAGE is mentioned (Marathi, Hindi, etc.), ALL books must be in that language.
- NO exceptions, NO close alternatives.

RETURN ONLY a valid JSON array of {max_recommendations} books in this format:
[
    {{
        "title": "Exact book title",
        "author": "Full author name",
        "description": "Specific explanation of how this book PERFECTLY matches '{user_query}'",
        "genre": "Primary genre (must match query)",
        "year_published": year_or_null,
        "rating": float_or_null,
        "language": "EXACT_LANGUAGE_FROM_QUERY",
        "target_audience": "children|young_adult|adult|general",
        "book_type": "fiction|non_fiction|biography|memoir|textbook|reference",
        "content_type": "novel|short_stories|poetry|essays|academic|self_help",
        "reading_level": "beginner|intermediate|advanced|expert"
    }}
]

CRITICAL: Return ONLY the JSON array, with no additional text, markdown, or explanations.
"""

    @staticmethod
    async def generate_recommendations(user_query: str, max_recommendations: int = 20) -> BookRecommendationResponse:
        """Generate book recommendations using Google Gemini API"""
        print(f"\n{'='*80}\n🎯 New recommendation request: '{user_query}' for {max_recommendations} books.\n{'='*80}\n")
        
        if not settings.gemini_api_key:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gemini API key not configured")
            
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            # FIX: Pass the user's max_recommendations to the prompt creator
            prompt = GeminiService.create_enhanced_prompt(user_query, max_recommendations)
            
            safety_settings = {
                "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
            }
            
            tokens_per_book = 300
            max_tokens = 500 + (max_recommendations * tokens_per_book)
            max_tokens = min(max_tokens, 8192) # Cap at a safe limit for the model
            
            response = await model.generate_content_async(
                prompt,
                generation_config={"temperature": 0.7, "max_output_tokens": max_tokens},
                safety_settings=safety_settings
            )
            
            content = response.text
            print(f"📡 Gemini API responded. Raw content preview: {content[:200]}...")
            
            # Clean and parse JSON
            content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
            
            try:
                books_data = json.loads(content)
                if not isinstance(books_data, list):
                    raise ValueError("Response is not a JSON array")
            except json.JSONDecodeError:
                # Attempt to extract JSON from a potentially messy string
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    books_data = json.loads(match.group(0))
                else:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse Gemini response as JSON")

            print(f"✅ Successfully parsed {len(books_data)} books from JSON")
            
            # If not enough books were returned, fill with synthetic ones
            if len(books_data) < max_recommendations:
                print(f"⚠️ Got {len(books_data)} books, need {max_recommendations}. Generating synthetic books...")
                existing_titles = {book.get('title', '').lower() for book in books_data}
                needed = max_recommendations - len(books_data)
                synthetic_books = GeminiService._generate_synthetic_books(user_query, needed, existing_titles)
                books_data.extend(synthetic_books)
            
            # Trim to the exact count requested
            books_data = books_data[:max_recommendations]
            
            books = []
            for book_data in books_data:
                try:
                    title = book_data.get('title', 'Unknown Title')
                    author = book_data.get('author', 'Unknown Author')
                    
                    cover_url = await GeminiService.fetch_book_cover(title, author)
                    if not cover_url:
                        cover_url = GeminiService.generate_fallback_cover(title, author)
                    
                    book_data['cover_image_url'] = cover_url
                    
                    validated_data = GeminiService._validate_and_normalize_filters(book_data)
                    books.append(Book(**validated_data))
                except Exception as e:
                    print(f"Error processing book data {book_data}: {str(e)}")
                    continue
            
            if not books:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No valid book recommendations could be generated")

            return BookRecommendationResponse(
                query=user_query,
                recommendations=books,
                generated_at=datetime.utcnow(),
                total_count=len(books)
            )
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating recommendations: {str(e)}")

    @staticmethod
    def _detect_query_genre(query_lower: str) -> str:
        """Helper to detect genre from a query using the predefined keyword mapping."""
        for genre, keywords in GENRE_KEYWORDS.items():
            if any(keyword in query_lower for keyword in keywords):
                return genre
        return "General"

    @staticmethod
    def _generate_synthetic_books(query: str, count: int, existing_titles: Set[str]) -> List[Dict]:
        """Generate synthetic book data to meet quantity requirements."""
        synthetic_books = []
        query_lower = query.lower()
        
        # REFINEMENT: Use the helper function for clean genre detection
        genre = GeminiService._detect_query_genre(query_lower)
        
        language = "English" # Default language
        for lang in ["Marathi", "Hindi", "Gujarati", "Spanish", "French"]:
            if lang.lower() in query_lower:
                language = lang
                break
        
        themes = ["Classic", "Modern", "Bestselling", "Acclaimed", "Essential", "Influential", "Timeless"]
        
        for i in range(count):
            theme = themes[i % len(themes)]
            base_title = f"{theme} {genre} Collection"
            title = f"{base_title} Vol. {i + 1}"
            
            # Ensure title is unique
            counter = 1
            while title.lower() in existing_titles:
                title = f"{base_title} Vol. {i + 1} (Copy {counter})"
                counter += 1
            existing_titles.add(title.lower())
            
            synthetic_books.append({
                "title": title,
                "author": "Various Authors",
                "description": f"A curated collection of {genre.lower()} works in {language} matching your request for '{query}'.",
                "genre": genre, "language": language, "year_published": 2020 + (i % 5),
                "rating": round(4.0 + (hash(title) % 10) / 10, 1),
                "target_audience": "adult" if genre in ["Horror", "Thriller/Suspense", "True Crime"] else "general",
                "book_type": "non_fiction" if genre in ["Biography/Memoir", "History", "Science (Non-Fiction)"] else "fiction",
                "content_type": "short_stories", "reading_level": "intermediate"
            })
            
        print(f"📚 Generated {len(synthetic_books)} synthetic books.")
        return synthetic_books

    @staticmethod
    def _normalize_value(value: Optional[str], valid_values: set, default: str) -> str:
        """A helper to normalize a string against a set of valid options."""
        if value and value in valid_values:
            return value
        
        value_lower = value.lower().strip() if value else ''
        for valid_option in valid_values:
            if valid_option == value_lower or valid_option.replace('_', ' ') == value_lower:
                return valid_option
        return default

    @staticmethod
    def _validate_and_normalize_filters(book_data: dict) -> dict:
        """Validate and normalize filter values for consistency using a helper."""
        # REFINEMENT: Simplified validation using the _normalize_value helper
        valid_languages = {"English", "Spanish", "French", "German", "Japanese", "Chinese", "Hindi", "Marathi"}
        valid_audiences = {"children", "young_adult", "adult", "general"}
        valid_book_types = {"fiction", "non_fiction", "biography", "memoir", "textbook", "reference"}
        valid_content_types = {"novel", "short_stories", "poetry", "essays", "academic", "self_help"}
        valid_reading_levels = {"beginner", "intermediate", "advanced", "expert"}
        
        book_data['language'] = GeminiService._normalize_value(book_data.get('language'), valid_languages, 'English')
        book_data['target_audience'] = GeminiService._normalize_value(book_data.get('target_audience'), valid_audiences, 'general')
        book_data['book_type'] = GeminiService._normalize_value(book_data.get('book_type'), valid_book_types, 'fiction')
        book_data['content_type'] = GeminiService._normalize_value(book_data.get('content_type'), valid_content_types, 'novel')
        book_data['reading_level'] = GeminiService._normalize_value(book_data.get('reading_level'), valid_reading_levels, 'intermediate')
        
        return book_data

    @staticmethod
    async def test_gemini_connection() -> bool:
        """Test if Gemini API is properly configured and accessible"""
        try:
            # FIX: Use a single, valid model name for the test
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            # Use async version in an async method
            response = await model.generate_content_async("Hello")
            return response.text is not None
        except Exception as e:
            print(f"Gemini connection error: {str(e)}")
            return False