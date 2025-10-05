from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Book(BaseModel):
    """Schema for individual book recommendation"""
    title: str
    author: str
    description: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    rating: Optional[float] = None
    cover_image_url: Optional[str] = None
    language: Optional[str] = None
    target_audience: Optional[str] = None
    book_type: Optional[str] = None
    content_type: Optional[str] = None
    reading_level: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Silent Patient",
                "author": "Alex Michaelides",
                "description": "A psychological thriller about a woman who refuses to speak after allegedly murdering her husband.",
                "genre": "Psychological Thriller",
                "year_published": 2019,
                "rating": 4.2,
                "cover_image_url": "https://example.com/cover.jpg",
                "language": "English",
                "target_audience": "adult",
                "book_type": "fiction",
                "content_type": "novel",
                "reading_level": "intermediate"
            }
        }


class BookRecommendationRequest(BaseModel):
    """Schema for book recommendation request"""
    query: str
    count: Optional[int] = None  # Frontend sends 'count'
    max_recommendations: Optional[int] = None  # Legacy field
    
    @property
    def requested_count(self) -> int:
        """Get the requested count from either field, default to 20"""
        return self.count or self.max_recommendations or 20
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "psychological thrillers with a twist ending",
                "count": 20
            }
        }


class BookRecommendationResponse(BaseModel):
    """Schema for book recommendation response"""
    query: str
    recommendations: List[Book]
    generated_at: datetime
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "psychological thrillers with a twist ending",
                "recommendations": [
                    {
                        "title": "The Silent Patient",
                        "author": "Alex Michaelides",
                        "description": "A psychological thriller about a woman who refuses to speak after allegedly murdering her husband.",
                        "genre": "Psychological Thriller",
                        "year_published": 2019,
                        "rating": 4.2
                    }
                ],
                "generated_at": "2023-01-01T12:00:00",
                "total_count": 1
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    status_code: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid request or server error",
                "status_code": 400
            }
        }