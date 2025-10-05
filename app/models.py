from beanie import Document, Indexed
from pydantic import Field
from typing import Optional


class User(Document):
    """
    Beanie Document model for User
    """
    username: Indexed(str, unique=True)  # type: ignore
    hashed_password: str
    
    class Settings:
        name = "users"  # MongoDB collection name