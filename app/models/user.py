from beanie import Document, Indexed
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(Document):
    """User model for MongoDB using Beanie ODM"""
    
    email: Indexed(EmailStr, unique=True)  # type: ignore
    username: Indexed(str, unique=True)  # type: ignore
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"  # MongoDB collection name
        
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "bookworm123",
                "full_name": "John Doe",
                "is_active": True
            }
        }
    }


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "bookworm123",
                "password": "securepassword123",
                "full_name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    }


class UserResponse(BaseModel):
    """Schema for user response (excluding sensitive data)"""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "60d5ecb54b24c8a5e8b4d2f1",
                "email": "user@example.com",
                "username": "bookworm123",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "last_login": "2023-01-01T12:00:00"
            }
        }
    }


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str
    user: UserResponse
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "60d5ecb54b24c8a5e8b4d2f1",
                    "email": "user@example.com",
                    "username": "bookworm123",
                    "full_name": "John Doe",
                    "is_active": True,
                    "created_at": "2023-01-01T00:00:00"
                }
            }
        }
    }