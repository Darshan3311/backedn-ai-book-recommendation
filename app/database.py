"""
Database initialization and connection management
"""

import motor.motor_asyncio
from beanie import init_beanie
from app.models.user import User
from app.models.saved_book import SavedBook
from app.config import settings


async def init_db():
    """
    Initialize the database connection for FastAPI using Beanie and Motor
    
    This function:
    1. Creates a Motor client using the MongoDB connection string from settings
    2. Initializes Beanie with the client, database name, and Document models
    3. Sets up the database for use throughout the application
    """
    
    # Create Motor client using the connection string from settings
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_connection_string)
    
    # Initialize Beanie with the client, database name, and list of Document models
    await init_beanie(
        database=client.book_recommendations,  # Database name
        document_models=[User, SavedBook]  # List of Beanie Document models
    )
    
    print("✅ Database connection initialized successfully")


async def close_db():
    """
    Close database connections (if needed for cleanup)
    """
    # Beanie/Motor handles connection cleanup automatically
    # This function is here for potential future cleanup needs
    pass