from beanie import Document
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

class SavedBook(Document):
    """Saved book model for storing user's favorite books"""
    user_id: ObjectId = Field(..., description="ID of the user who saved this book")
    title: str = Field(..., description="Book title")
    author: str = Field(..., description="Book author")
    genre: str = Field(..., description="Book genre")
    summary: str = Field(..., description="Book summary/description")
    cover_image_url: Optional[str] = Field(None, description="URL of the book cover image")
    rating: Optional[float] = Field(None, description="Book rating")
    isbn: Optional[str] = Field(None, description="Book ISBN")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    saved_at: datetime = Field(default_factory=datetime.utcnow, description="When the book was saved")
    
    class Settings:
        name = "saved_books"
        
    model_config = {
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "user_id": "507f1f77bcf86cd799439011",
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "genre": "Classic Literature",
                "summary": "A classic American novel set in the Jazz Age...",
                "cover_image_url": "https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg",
                "rating": 4.2,
                "isbn": "9780743273565",
                "publication_year": 1925,
                "saved_at": "2025-09-30T10:00:00Z"
            }
        }
    }

class SavedBookCreate(BaseModel):
    """Schema for creating a saved book"""
    title: str
    author: str
    genre: str
    summary: str
    cover_image_url: Optional[str] = None
    rating: Optional[float] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None

class SavedBookResponse(BaseModel):
    """Schema for saved book response"""
    id: str
    user_id: str
    title: str
    author: str
    genre: str
    summary: str
    cover_image_url: Optional[str] = None
    rating: Optional[float] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    saved_at: datetime
    
    model_config = {"from_attributes": True}