"""
Saved Books router for managing user's saved book recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from app.models.saved_book import SavedBook, SavedBookCreate, SavedBookResponse
from app.models.user import User
from app.security import get_current_user

router = APIRouter(prefix="/saved-books", tags=["saved-books"])

@router.post("/", response_model=SavedBookResponse, status_code=status.HTTP_201_CREATED)
async def save_book(
    saved_book_data: SavedBookCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Save a book to the user's collection
    
    Args:
        saved_book_data: Book data to save
        current_user: Currently authenticated user
        
    Returns:
        SavedBookResponse: The saved book data
        
    Raises:
        HTTPException: If book is already saved or save operation fails
    """
    try:
        # Check if book is already saved by this user
        existing_book = await SavedBook.find_one({
            "user_id": current_user.id,
            "title": saved_book_data.title,
            "author": saved_book_data.author
        })
        
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book is already saved to your collection"
            )
        
        # Create new saved book
        saved_book = SavedBook(
            user_id=current_user.id,
            **saved_book_data.model_dump()
        )
        
        # Save to database
        await saved_book.insert()
        
        # Return the saved book data
        return SavedBookResponse(
            id=str(saved_book.id),
            user_id=str(saved_book.user_id),
            **saved_book_data.model_dump(),
            saved_at=saved_book.saved_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save book: {str(e)}"
        )

@router.get("/", response_model=List[SavedBookResponse])
async def get_saved_books(
    current_user: User = Depends(get_current_user)
):
    """
    Get all saved books for the current user
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        List[SavedBookResponse]: List of user's saved books
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Find all saved books for the current user
        saved_books = await SavedBook.find({"user_id": current_user.id}).sort("-saved_at").to_list()
        
        # Convert to response format
        return [
            SavedBookResponse(
                id=str(book.id),
                user_id=str(book.user_id),
                title=book.title,
                author=book.author,
                genre=book.genre,
                summary=book.summary,
                cover_image_url=book.cover_image_url,
                rating=book.rating,
                isbn=book.isbn,
                publication_year=book.publication_year,
                saved_at=book.saved_at
            )
            for book in saved_books
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved books: {str(e)}"
        )

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_book(
    book_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Remove a book from the user's saved collection
    
    Args:
        book_id: ID of the saved book to remove
        current_user: Currently authenticated user
        
    Raises:
        HTTPException: If book not found or removal fails
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(book_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid book ID format"
            )
        
        # Find the saved book
        saved_book = await SavedBook.find_one({
            "_id": ObjectId(book_id),
            "user_id": current_user.id
        })
        
        if not saved_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved book not found"
            )
        
        # Delete the saved book
        await saved_book.delete()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove saved book: {str(e)}"
        )

@router.get("/check/{title}/{author}", response_model=dict)
async def check_if_book_saved(
    title: str,
    author: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if a specific book is already saved by the user
    
    Args:
        title: Book title
        author: Book author
        current_user: Currently authenticated user
        
    Returns:
        dict: {"is_saved": bool, "saved_book_id": str or None}
    """
    try:
        saved_book = await SavedBook.find_one({
            "user_id": current_user.id,
            "title": title,
            "author": author
        })
        
        return {
            "is_saved": saved_book is not None,
            "saved_book_id": str(saved_book.id) if saved_book else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check saved book status: {str(e)}"
        )