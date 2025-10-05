import json
import aiohttp
import urllib.parse
from typing import List, Optional
from datetime import datetime
from openai import AsyncOpenAI
from fastapi import HTTPException, status
from app.models.book import Book, BookRecommendationResponse
from app.config import settings

# Initialize OpenAI client with API key from settings (if available)
client = None
if settings.openai_api_key:
    client = AsyncOpenAI(api_key=settings.openai_api_key)


class OpenAIService:
    """Service for generating book recommendations using OpenAI API"""
    
    @staticmethod
    async def fetch_book_cover(title: str, author: str) -> Optional[str]:
        """Fetch real book cover from Google Books API"""
        try:
            # Clean and encode the search query
            query = f'intitle:"{title}" inauthor:"{author}"'
            encoded_query = urllib.parse.quote(query)
            
            # Google Books API endpoint
            url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=1"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('totalItems', 0) > 0:
                            volume = data['items'][0]
                            volume_info = volume.get('volumeInfo', {})
                            image_links = volume_info.get('imageLinks', {})
                            
                            # Try different image sizes (large, medium, small, thumbnail)
                            for size in ['large', 'medium', 'small', 'thumbnail']:
                                if size in image_links:
                                    # Convert to HTTPS for security
                                    cover_url = image_links[size].replace('http:', 'https:')
                                    return cover_url
                                    
        except Exception as e:
            print(f"Error fetching cover for '{title}' by '{author}': {str(e)}")
            
        return None
    
    @staticmethod
    def generate_fallback_cover(title: str, author: str) -> str:
        """Generate a stylish fallback cover image"""
        # Create a more attractive placeholder
        colors = [
            "1a202c", "2d3748", "2b6cb0", "3182ce", "0c4a6e",
            "065f46", "047857", "0f766e", "155e75", "0e7490"
        ]
        
        # Generate consistent color based on title
        color_index = hash(title.lower()) % len(colors)
        bg_color = colors[color_index]
        
        # Create clean title and author text
        title_clean = title[:25].replace(' ', '+')
        author_clean = f"by+{author[:20].replace(' ', '+')}"
        
        return f"https://via.placeholder.com/300x400/{bg_color}/ffffff.png?text={title_clean}%0A%0A{author_clean}"
    
    @staticmethod
    def create_prompt(user_query: str, max_recommendations: int = 5) -> str:
        """Create a structured prompt for OpenAI to generate book recommendations"""
        return f"""You are a knowledgeable book recommendation expert. Based on the user's request, provide {max_recommendations} book recommendations that match their criteria.

User's request: "{user_query}"

Please provide your response as a valid JSON array where each book is an object with the following structure:
{{
    "title": "Book Title",
    "author": "Author Name", 
    "description": "A compelling 2-3 sentence description of the book and why it matches the request",
    "genre": "Primary genre",
    "year_published": year as integer (if known, otherwise null),
    "rating": average rating as float between 1-5 (if known, otherwise null),
    "language": "Primary language (e.g., 'English', 'Hindi', 'Spanish', 'French', 'German', 'Japanese', 'Chinese', etc.)",
    "target_audience": "Target audience (e.g., 'children', 'young_adult', 'adult', 'general')",
    "book_type": "Book type (e.g., 'fiction', 'non_fiction', 'biography', 'memoir', 'textbook', 'reference')",
    "content_type": "Content type (e.g., 'novel', 'short_stories', 'poetry', 'essays', 'academic', 'self_help')",
    "reading_level": "Reading difficulty (e.g., 'beginner', 'intermediate', 'advanced', 'expert')"
}}

Important guidelines:
1. Only recommend real, published books
2. Ensure descriptions are engaging and explain why each book fits the request
3. Vary the recommendations to show different perspectives within the requested criteria
4. Always include ALL required fields including language, target_audience, book_type, content_type, and reading_level
5. For language: Use the original language of the book (English, Hindi, Spanish, French, etc.)
6. For target_audience: Consider age appropriateness and content complexity
7. For book_type: Categorize as fiction, non-fiction, biography, memoir, textbook, or reference
8. For content_type: Specify the format (novel, short stories, poetry, essays, academic, self-help, etc.)
9. For reading_level: Assess based on vocabulary, sentence complexity, and subject matter difficulty
10. If the request is vague, interpret it broadly but stay relevant
11. Response must be valid JSON format only, no additional text

Provide exactly {max_recommendations} recommendations as a JSON array:"""
    
    @staticmethod
    async def generate_recommendations(
        user_query: str, 
        max_recommendations: int = 5
    ) -> BookRecommendationResponse:
        """Generate book recommendations using OpenAI API"""
        
        if not settings.openai_api_key or not client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )
        
        try:
            # Create the prompt
            prompt = OpenAIService.create_prompt(user_query, max_recommendations)
            
            # Call OpenAI API
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful book recommendation assistant that provides accurate, well-researched book suggestions in JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Empty response from OpenAI"
                )
            
            # Parse JSON response
            try:
                recommendations_data = json.loads(content)
                
                # Handle different response formats
                if isinstance(recommendations_data, dict):
                    if "recommendations" in recommendations_data:
                        books_data = recommendations_data["recommendations"]
                    elif "books" in recommendations_data:
                        books_data = recommendations_data["books"]
                    else:
                        # If it's a dict but not wrapped, assume it's a single book
                        books_data = [recommendations_data]
                elif isinstance(recommendations_data, list):
                    books_data = recommendations_data
                else:
                    raise ValueError("Invalid response format")
                
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to parse OpenAI response as JSON: {str(e)}"
                )
            
            # Convert to Book objects and fetch real cover images
            books = []
            for book_data in books_data[:max_recommendations]:  # Ensure we don't exceed limit
                try:
                    # Fetch real book cover
                    title = book_data.get('title', '')
                    author = book_data.get('author', '')
                    
                    # Try to get real cover image
                    cover_url = await OpenAIService.fetch_book_cover(title, author)
                    
                    # Use fallback if real cover not found
                    if not cover_url:
                        cover_url = OpenAIService.generate_fallback_cover(title, author)
                    
                    # Add cover URL to book data
                    book_data['cover_image_url'] = cover_url
                    
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
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating recommendations: {str(e)}"
            )
    
    @staticmethod
    async def test_openai_connection() -> bool:
        """Test if OpenAI API is properly configured and accessible"""
        try:
            if not client:
                return False
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return response.choices[0].message.content is not None
        except Exception:
            return False