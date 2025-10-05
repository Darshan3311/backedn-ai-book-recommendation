from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    """Pydantic model for user creation"""
    username: str
    email: str
    password: str


class UserPublic(BaseModel):
    """Pydantic model to safely return user data"""
    id: str
    username: str
    email: str


class Token(BaseModel):
    """Pydantic model for authentication token"""
    access_token: str
    token_type: str


class BookQuery(BaseModel):
    """Pydantic model for book query requests with comprehensive filters"""
    query: str
    count: int = 15  # Minimum 15 books, use 100+ for comprehensive results
    get_all_available: bool = False  # Set to True to get maximum available books
    
    # Language filters
    language: Optional[str] = None  # e.g., "English", "Spanish", "French", "Japanese", etc.
    
    # Age group filters  
    age_group: Optional[str] = None  # "children", "young_adult", "adult", "senior"
    target_audience: Optional[str] = None  # "kids", "teens", "men", "women", "couples", "families"
    
    # Book type filters
    book_type: Optional[str] = None  # "fiction", "non_fiction", "textbook", "comic", "manga", "graphic_novel"
    
    # Content filters
    content_type: Optional[str] = None  # "educational", "entertainment", "self_help", "academic", "professional"
    
    # Difficulty/Reading level
    reading_level: Optional[str] = None  # "beginner", "intermediate", "advanced", "expert"
    
    # Special categories
    special_category: Optional[str] = None  # "bestseller", "award_winner", "classic", "new_release", "indie"


class Book(BaseModel):
    """Pydantic model for book recommendations with enhanced metadata"""
    title: str
    author: str
    genre: str
    brief_summary: str
    short_description: str
    cover_image_url: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    rating: Optional[float] = None
    
    # Enhanced filtering metadata
    language: Optional[str] = "English"
    age_group: Optional[str] = None  # "children", "young_adult", "adult", "senior"
    target_audience: Optional[str] = None  # "kids", "teens", "men", "women", "couples", "families"
    book_type: Optional[str] = "fiction"  # "fiction", "non_fiction", "textbook", "comic", "manga", "graphic_novel"
    content_type: Optional[str] = "entertainment"  # "educational", "entertainment", "self_help", "academic", "professional"
    reading_level: Optional[str] = "intermediate"  # "beginner", "intermediate", "advanced", "expert"
    page_count: Optional[int] = None
    series_info: Optional[str] = None  # If part of a series