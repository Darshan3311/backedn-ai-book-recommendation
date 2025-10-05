import json
import re
import aiohttp
import urllib.parse
from typing import List, Optional
from datetime import datetime
import google.generativeai as genai
from fastapi import HTTPException, status
from app.models.book import Book, BookRecommendationResponse
from app.config import settings

# Configure Gemini API
genai.configure(api_key=settings.gemini_api_key)


class GeminiService:
    """Service for generating book recommendations using Google Gemini API"""
    
    @staticmethod
    async def fetch_book_cover(title: str, author: str) -> Optional[str]:
        """Fetch real book cover from Google Books API with multiple search strategies"""
        try:
            # Multiple search strategies for better results
            search_queries = [
                f'intitle:"{title}" inauthor:"{author}"',  # Exact match
                f'{title} {author}',  # Simple search
                f'intitle:{title.split()[0]} inauthor:{author.split()[0]}' if ' ' in title and ' ' in author else None,  # First words only
                title  # Title only as last resort
            ]
            
            # Remove None values
            search_queries = [q for q in search_queries if q]
            
            for query in search_queries:
                encoded_query = urllib.parse.quote(query)
                url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=3"
                
                print(f"Searching for cover: {query}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get('totalItems', 0) > 0:
                                # Try each result until we find a good cover
                                for item in data['items'][:3]:  # Check up to 3 results
                                    volume_info = item.get('volumeInfo', {})
                                    image_links = volume_info.get('imageLinks', {})
                                    
                                    # Try different image sizes (high quality first)
                                    for size in ['extraLarge', 'large', 'medium', 'small', 'thumbnail']:
                                        if size in image_links:
                                            cover_url = image_links[size]
                                            # Convert to HTTPS and ensure proper format
                                            cover_url = cover_url.replace('http:', 'https:')
                                            cover_url = cover_url.replace('&edge=curl', '')  # Remove curl effect
                                            cover_url = cover_url.replace('zoom=1', 'zoom=0')  # No zoom
                                            
                                            print(f"Found cover URL: {cover_url}")
                                            return cover_url
                            else:
                                print(f"No results for query: {query}")
                        else:
                            print(f"API request failed with status: {response.status}")
                            
        except Exception as e:
            print(f"Error fetching cover for '{title}' by '{author}': {str(e)}")
            
        print(f"No cover found for '{title}' by '{author}', using fallback")
        return None
    
    @staticmethod
    def generate_fallback_cover(title: str, author: str) -> str:
        """Generate a stylish fallback cover image using multiple services"""
        try:
            # Modern gradient colors for better aesthetics
            colors = [
                "667eea", "764ba2", "f093fb", "f5576c", "4facfe",
                "43e97b", "38ef7d", "eea2a2", "bbc1c1", "57c6e1",
                "b721ff", "21d4fd", "b721ff", "21d4fd", "fcb045"
            ]
            
            # Generate consistent color based on title
            color_index = hash(title.lower()) % len(colors)
            bg_color = colors[color_index]
            
            # Create clean, URL-safe text
            title_clean = title[:20].replace(' ', '%20').replace('&', 'and')
            author_clean = author[:15].replace(' ', '%20').replace('&', 'and')
            
            # Try multiple fallback services
            fallback_urls = [
                f"https://via.placeholder.com/300x400/{bg_color}/ffffff.png?text={title_clean}%0A%0A{author_clean}",
                f"https://dummyimage.com/300x400/{bg_color}/ffffff.png&text={title_clean}+{author_clean}",
                f"https://picsum.photos/300/400?random={hash(title) % 1000}"  # Random nature image as backup
            ]
            
            # Return the first URL (placeholder.com is most reliable)
            print(f"Generated fallback cover for '{title}': {fallback_urls[0]}")
            return fallback_urls[0]
            
        except Exception as e:
            print(f"Error generating fallback cover: {str(e)}")
            # Absolute fallback - simple solid color
            return "https://via.placeholder.com/300x400/4A5568/ffffff.png?text=Book+Cover"
    
    @staticmethod
    def create_enhanced_prompt(user_query: str, max_recommendations: int = 5) -> str:
        """Create a comprehensive prompt for Gemini to generate contextually relevant book recommendations"""
        return f"""You are an expert librarian and book recommendation specialist with deep knowledge of world literature across all languages, genres, and reading levels. A user has requested book recommendations with this query: "{user_query}"

CRITICAL: You MUST provide EXACTLY {max_recommendations} book recommendations. Do not provide more or fewer books. If you cannot find {max_recommendations} perfect matches, include good alternatives that are close to the request.

Please analyze the user's request carefully and provide EXACTLY {max_recommendations} highly relevant book recommendations. You MUST follow the exact filter specifications below to ensure consistent filtering.

For each book, you must provide complete and accurate information in the following JSON format:

[
    {{
        "title": "Exact book title",
        "author": "Author's full name",
        "description": "2-3 engaging sentences describing the book and why it perfectly matches the user's request",
        "genre": "Primary genre/category",
        "year_published": publication_year_as_integer_or_null,
        "rating": average_rating_as_float_1_to_5_or_null,
        "language": "Primary language of the book",
        "target_audience": "Target audience category",
        "book_type": "Type of book",
        "content_type": "Content format",
        "reading_level": "Reading difficulty level"
    }}
]

CRITICAL REQUIREMENTS for each field:

1. **title & author**: Must be real, published books only. No fictional titles.

2. **description**: Write compelling descriptions that clearly explain why each book matches the user's specific request. Make it personal and relevant.

3. **language**: MUST use exactly one of these values (case-sensitive):
   - "English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian", "Japanese", "Chinese", "Korean", "Arabic"
   - "Hindi", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati", "Urdu", "Punjabi", "Sanskrit"
   - Use the book's original language. If uncertain, default to "English"

4. **target_audience**: MUST use exactly one of these values (case-sensitive):
   - "children" (ages 3-12)
   - "young_adult" (ages 13-17)
   - "adult" (ages 18+)
   - "general" (suitable for multiple age groups)

5. **book_type**: MUST use exactly one of these values (case-sensitive):
   - "fiction" (novels, stories, fantasy, sci-fi, etc.)
   - "non_fiction" (informational, educational, factual)
   - "biography" (life stories of real people)
   - "memoir" (personal accounts)
   - "textbook" (educational/academic)
   - "reference" (dictionaries, encyclopedias, etc.)

6. **content_type**: MUST use exactly one of these values (case-sensitive):
   - "novel" (full-length fiction)
   - "short_stories" (collection of short fiction)
   - "poetry" (poems, verse)
   - "essays" (essay collections)
   - "academic" (scholarly work)
   - "self_help" (personal development)

7. **reading_level**: MUST use exactly one of these values (case-sensitive):
   - "beginner" (simple vocabulary, basic concepts)
   - "intermediate" (moderate vocabulary, some complex ideas)
   - "advanced" (sophisticated vocabulary, complex themes)
   - "expert" (highly specialized, academic level)

SPECIAL INSTRUCTIONS:

- CRITICAL: If the user specifies a language (like Hindi, Marathi, Spanish, etc.), ALL books MUST be in that exact language
- If they mention age or audience, match the target_audience exactly
- If they specify fiction/non-fiction, respect that in book_type exactly
- If they want easy/difficult books, adjust reading_level exactly
- If they specify content format (novel, poetry, etc.), match content_type exactly
- Parse filter context from queries like "Hindi fiction novels for adults" -> language=Hindi, book_type=fiction, target_audience=adult
- ALWAYS prioritize user's explicit filter requirements over general recommendations
- Ensure all filter fields are populated with appropriate values
- Double-check that each book genuinely matches ALL specified criteria
- If no books exist matching exact criteria, find the closest matches but still respect language requirements

LANGUAGE PRIORITY: If language is specified, it is the MOST IMPORTANT filter - never recommend books in other languages.

CRITICAL JSON FORMATTING RULES:
- Escape all special characters properly (quotes, newlines, backslashes)
- Use proper JSON escaping for any quotes in descriptions: use \\" for quotes inside strings
- Keep descriptions concise to avoid formatting issues
- Do NOT include any text outside the JSON array
- Ensure the JSON is valid and can be parsed

Your response must be a valid JSON array only, with no additional text or explanations. Make sure each recommendation is perfectly suited to the user's specific request and has complete metadata for effective filtering."""

    @staticmethod
    async def generate_recommendations(
        user_query: str, 
        max_recommendations: int = 5
    ) -> BookRecommendationResponse:
        """Generate book recommendations using Google Gemini API"""
        
        print(f"\n{'='*80}")
        print(f"🎯 New recommendation request:")
        print(f"   Query: {user_query}")
        print(f"   Max recommendations: {max_recommendations}")
        print(f"{'='*80}\n")
        
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Gemini API key not configured"
            )
        
        try:
            # Try gemini-2.0-flash-exp first (experimental with relaxed filters)
            # If that fails, use the standard gemini-1.5-flash
            model_names = ['gemini-2.0-flash-exp', 'gemini-1.5-flash']
            content = None  # Initialize to track if we got a response
            model = None
            safety_settings = None
            
            for model_name in model_names:
                try:
                    print(f"🤖 Using model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    
                    # Create the enhanced prompt
                    prompt = GeminiService.create_enhanced_prompt(user_query, max_recommendations)
                    
                    # Configure safety settings - use BLOCK_ONLY_HIGH for better results
                    try:
                        from google.generativeai.types import HarmCategory, HarmBlockThreshold
                        
                        # BLOCK_ONLY_HIGH allows most content through
                        safety_settings = {
                            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                        }
                        print(f"✅ Safety settings: BLOCK_ONLY_HIGH")
                    except Exception as e:
                        print(f"⚠️ Could not set safety settings: {e}")
                        safety_settings = None
                    
                    # Calculate appropriate token limit based on book count
                    # Each book needs ~250 tokens, add buffer for JSON formatting
                    tokens_per_book = 300
                    base_tokens = 500  # Buffer for JSON structure
                    max_tokens = base_tokens + (max_recommendations * tokens_per_book)
                    # Cap at 8000 (Gemini's limit)
                    max_tokens = min(max_tokens, 8000)
                    
                    print(f"📊 Requesting {max_recommendations} books with {max_tokens} max tokens")
                    
                    # Generate response
                    response = model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            max_output_tokens=max_tokens,
                            candidate_count=1,
                        ),
                        safety_settings=safety_settings
                    )
                    
                    print(f"📡 Gemini API responded")
                    
                    # Try to get response text
                    try:
                        content = response.text
                        print(f"✅ Got response text ({len(content)} characters)")
                        break  # Success! Exit model loop
                        
                    except Exception as e:
                        # Check if blocked by safety
                        if hasattr(response, 'candidates') and response.candidates:
                            finish_reason = response.candidates[0].finish_reason if hasattr(response.candidates[0], 'finish_reason') else None
                            if finish_reason == 2:
                                print(f"⚠️ {model_name} blocked by safety filter (finish_reason=2)")
                                if model_name == model_names[-1]:  # Last model
                                    # All models failed, return helpful error
                                    raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail=f"Unable to generate recommendations for '{user_query}'. This query triggers content safety filters. Try alternative search terms like 'thriller', 'mystery', or 'suspense'."
                                    )
                                else:
                                    print(f"🔄 Trying next model...")
                                    continue  # Try next model
                        raise e
                        
                except HTTPException:
                    raise
                except Exception as model_error:
                    print(f"❌ Error with {model_name}: {str(model_error)}")
                    if model_name == model_names[-1]:
                        raise
                    else:
                        print(f"🔄 Trying next model...")
                        continue
            
            # Check if we got content from any model
            if not content:
                print(f"⚠️ No content retrieved from any model")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unable to generate recommendations - all models failed or were blocked"
                )
            
            # Successfully got content, now parse it
            print(f"� Raw content preview: {content[:200]}...")

            # Clean the response - remove any markdown formatting
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            print(f"🧹 Cleaned response, attempting JSON parse...")
            
            # Parse JSON response with error recovery
            try:
                books_data = json.loads(content)
                
                if not isinstance(books_data, list):
                    print(f"⚠️ Response is not a list, it's a {type(books_data)}")
                    raise ValueError("Response must be a JSON array")
                
                print(f"✅ Successfully parsed {len(books_data)} books from JSON")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {str(e)}")
                print(f"Full response content:\n{content}")
                
                # Try to fix common JSON issues
                try:
                    # Fix common issues: unescaped quotes, newlines in strings, etc.
                    import re
                    
                    # Try to extract just the array part if there's extra text
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        content = match.group(0)
                        print(f"🔧 Extracted array from response, retrying parse...")
                        books_data = json.loads(content)
                        print(f"✅ Successfully parsed after extraction: {len(books_data)} books")
                    else:
                        raise e
                        
                except Exception as retry_error:
                    print(f"❌ Retry parsing also failed: {str(retry_error)}")
                    
                    # Last resort: Ask Gemini to return valid JSON
                    print(f"🔄 Requesting Gemini to fix JSON formatting...")
                    fix_prompt = f"Fix this malformed JSON and return ONLY valid JSON array with no extra text:\n{content[:1000]}"
                    
                    try:
                        fix_response = model.generate_content(
                            fix_prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=2500,
                            ),
                            safety_settings=safety_settings
                        )
                        fixed_content = fix_response.text.strip()
                        if fixed_content.startswith('```json'):
                            fixed_content = fixed_content[7:]
                        if fixed_content.startswith('```'):
                            fixed_content = fixed_content[3:]
                        if fixed_content.endswith('```'):
                            fixed_content = fixed_content[:-3]
                        fixed_content = fixed_content.strip()
                        
                        books_data = json.loads(fixed_content)
                        print(f"✅ Successfully parsed after fix: {len(books_data)} books")
                    except Exception as final_error:
                        print(f"❌ All parsing attempts failed: {str(final_error)}")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to parse Gemini response as JSON after multiple attempts: {str(e)}"
                        )
            
            # Convert to Book objects and fetch real cover images
            books = []
            for book_data in books_data[:max_recommendations]:  # Ensure we don't exceed limit
                try:
                    # Fetch real book cover
                    title = book_data.get('title', '')
                    author = book_data.get('author', '')
                    
                    # Try to get real cover image
                    cover_url = await GeminiService.fetch_book_cover(title, author)
                    
                    # Use fallback if real cover not found
                    if not cover_url:
                        cover_url = GeminiService.generate_fallback_cover(title, author)
                    
                    # Add cover URL to book data
                    book_data['cover_image_url'] = cover_url
                    
                    # Validate and normalize filter fields
                    book_data = GeminiService.validate_and_normalize_filters(book_data)
                    
                    book = Book(**book_data)
                    books.append(book)
                except Exception as e:
                    # Log the error but continue with other books
                    print(f"Error creating book from data {book_data}: {str(e)}")
                    continue
            
            if not books:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No valid book recommendations could be generated"
                )
            
            # Create response
            return BookRecommendationResponse(
                query=user_query,
                recommendations=books,
                generated_at=datetime.utcnow(),
                total_count=len(books)
            )
            
        except Exception as e:
            print(f"❌ Error generating recommendations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating recommendations: {str(e)}"
            )
    
    @staticmethod
    def validate_and_normalize_filters(book_data: dict) -> dict:
        """Validate and normalize filter values to ensure consistency"""
        
        # Define valid filter values
        valid_languages = {
            "English", "Spanish", "French", "German", "Italian", "Portuguese", "Russian", 
            "Japanese", "Chinese", "Korean", "Arabic", "Hindi", "Bengali", "Tamil", 
            "Telugu", "Marathi", "Gujarati", "Urdu", "Punjabi", "Sanskrit"
        }
        
        valid_audiences = {"children", "young_adult", "adult", "general"}
        valid_book_types = {"fiction", "non_fiction", "biography", "memoir", "textbook", "reference"}
        valid_content_types = {"novel", "short_stories", "poetry", "essays", "academic", "self_help"}
        valid_reading_levels = {"beginner", "intermediate", "advanced", "expert"}
        
        # Normalize and validate language
        language = book_data.get('language', 'English')
        if language not in valid_languages:
            # Try to find closest match or default to English
            language_lower = language.lower() if language else ''
            for valid_lang in valid_languages:
                if valid_lang.lower() == language_lower:
                    language = valid_lang
                    break
            else:
                language = 'English'
        book_data['language'] = language
        
        # Normalize and validate target_audience
        target_audience = book_data.get('target_audience', 'general')
        if target_audience not in valid_audiences:
            target_audience_lower = target_audience.lower() if target_audience else ''
            for valid_audience in valid_audiences:
                if valid_audience == target_audience_lower:
                    target_audience = valid_audience
                    break
            else:
                target_audience = 'general'
        book_data['target_audience'] = target_audience
        
        # Normalize and validate book_type
        book_type = book_data.get('book_type', 'fiction')
        if book_type not in valid_book_types:
            book_type_lower = book_type.lower() if book_type else ''
            # Handle common variations
            if 'non-fiction' in book_type_lower or 'nonfiction' in book_type_lower:
                book_type = 'non_fiction'
            elif 'fiction' in book_type_lower:
                book_type = 'fiction'
            else:
                for valid_type in valid_book_types:
                    if valid_type.replace('_', '-') == book_type_lower or valid_type == book_type_lower:
                        book_type = valid_type
                        break
                else:
                    book_type = 'fiction'
        book_data['book_type'] = book_type
        
        # Normalize and validate content_type
        content_type = book_data.get('content_type', 'novel')
        if content_type not in valid_content_types:
            content_type_lower = content_type.lower() if content_type else ''
            for valid_content in valid_content_types:
                if valid_content.replace('_', ' ') == content_type_lower or valid_content == content_type_lower:
                    content_type = valid_content
                    break
            else:
                content_type = 'novel'
        book_data['content_type'] = content_type
        
        # Normalize and validate reading_level
        reading_level = book_data.get('reading_level', 'intermediate')
        if reading_level not in valid_reading_levels:
            reading_level_lower = reading_level.lower() if reading_level else ''
            for valid_level in valid_reading_levels:
                if valid_level == reading_level_lower:
                    reading_level = valid_level
                    break
            else:
                reading_level = 'intermediate'
        book_data['reading_level'] = reading_level
        
        return book_data
    
    @staticmethod
    async def test_gemini_connection() -> bool:
        """Test if Gemini API is properly configured and accessible"""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content("Hello")
            return response.text is not None
        except Exception as e:
            print(f"Gemini connection error: {str(e)}")
            return False