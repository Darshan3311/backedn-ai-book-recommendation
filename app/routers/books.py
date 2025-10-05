from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.book import BookRecommendationRequest, BookRecommendationResponse
from app.models.user import User
from app.security import get_current_user
from app.services.gemini_service import GeminiService
from typing import Optional

router = APIRouter(prefix="/books", tags=["Book Recommendations"])


@router.post("/recommendations", response_model=BookRecommendationResponse)
async def get_book_recommendations(
    request: BookRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate book recommendations based on user query using Google Gemini
    
    - **query**: Natural language description of desired books
    - **max_recommendations**: Maximum number of books to recommend (default: 15, max: 150)
    
    Requires: Valid JWT token in Authorization header
    
    Examples of queries:
    - "psychological thrillers with a twist ending"
    - "sci-fi books about space exploration"
    - "romance novels set in historical periods"
    - "mystery books similar to Agatha Christie"
    - "fantasy books with strong female protagonists"
    """
    
    # Validate input
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    # Use the requested_count property which handles both 'count' and 'max_recommendations'
    # Allow up to 150 books (reasonable limit)
    max_recs = min(request.requested_count, 150)
    
    print(f"📊 Book recommendations request:")
    print(f"   Query: {request.query}")
    print(f"   Count from frontend: {request.count}")
    print(f"   Max recommendations (legacy): {request.max_recommendations}")
    print(f"   Final count to use: {max_recs}")
    
    try:
        # Generate recommendations using Gemini
        recommendations = await GeminiService.generate_recommendations(
            user_query=request.query,
            max_recommendations=max_recs
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/recommendations/search")
async def search_book_recommendations(
    q: str = Query(..., description="Search query for book recommendations", min_length=3),
    limit: Optional[int] = Query(5, description="Number of recommendations to return", ge=1, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    Search for book recommendations using query parameters (alternative to POST)
    
    - **q**: Search query (minimum 3 characters)
    - **limit**: Number of recommendations (1-10, default: 5)
    
    Requires: Valid JWT token in Authorization header
    """
    
    try:
        # Generate recommendations using OpenAI
        recommendations = await OpenAIService.generate_recommendations(
            user_query=q,
            max_recommendations=limit
        )
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/health")
async def check_health():
    """
    Health check endpoint for the books service
    
    Checks if OpenAI API is accessible
    """
    
    try:
        # Test OpenAI connection
        openai_status = await OpenAIService.test_openai_connection()
        
        return {
            "status": "healthy" if openai_status else "degraded",
            "openai_api": "connected" if openai_status else "disconnected",
            "message": "Book recommendation service is running"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "openai_api": "error",
            "error": str(e),
            "message": "Book recommendation service encountered an error"
        }


@router.post("/test-filters")
async def test_filter_generation(
    request: BookRecommendationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint to test filter generation and validation
    Returns detailed information about generated books and their filter metadata
    """
    try:
        # Generate recommendations (allow more for debugging)
        recommendations = await GeminiService.generate_recommendations(
            user_query=request.query,
            max_recommendations=min(request.max_recommendations or 10, 150)
        )
        
        # Add debugging information
        debug_info = {
            "query": request.query,
            "total_books": len(recommendations.recommendations),
            "books_with_debug": []
        }
        
        for book in recommendations.recommendations:
            book_debug = {
                "title": book.title,
                "author": book.author,
                "filter_metadata": {
                    "language": book.language,
                    "target_audience": book.target_audience,
                    "book_type": book.book_type,
                    "content_type": book.content_type,
                    "reading_level": book.reading_level
                },
                "missing_filters": [
                    field for field in ["language", "target_audience", "book_type", "content_type", "reading_level"]
                    if not getattr(book, field, None)
                ]
            }
            debug_info["books_with_debug"].append(book_debug)
        
        # Collect unique filter values
        debug_info["unique_filter_values"] = {
            "languages": list(set(book.language for book in recommendations.recommendations if book.language)),
            "target_audiences": list(set(book.target_audience for book in recommendations.recommendations if book.target_audience)),
            "book_types": list(set(book.book_type for book in recommendations.recommendations if book.book_type)),
            "content_types": list(set(book.content_type for book in recommendations.recommendations if book.content_type)),
            "reading_levels": list(set(book.reading_level for book in recommendations.recommendations if book.reading_level))
        }
        
        return debug_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in filter test: {str(e)}"
        )