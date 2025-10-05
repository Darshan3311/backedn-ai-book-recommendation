# Create the main FastAPI application file
# 1. Import FastAPI, CORSMiddleware, the `init_db` function, and the auth and recommendations routers
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import auth_router, recommendations_router
from app.routers.saved_books import router as saved_books_router
from app.routers.books import router as books_router


# 4. Add a startup event handler that calls `init_db`
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager with startup event handler
    """
    # Startup - call init_db
    print("🚀 Starting Book Recommendations API...")
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {str(e)}")
        raise
    
    print("🎉 Book Recommendations API is ready!")
    yield
    
    # Shutdown
    print("👋 Shutting down Book Recommendations API...")


# 2. Create the FastAPI app instance
app = FastAPI(
    title="AI Book Recommendations API",
    description="Get personalized book recommendations using AI",
    version="1.0.0",
    lifespan=lifespan
)

# 3. Configure CORS middleware to allow requests from the frontend's origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "https://frontend-ai-book-recommendation-3.onrender.com",
        "https://frontend-ai-book-recommendation.onrender.com",
        "https://backedn-ai-book-recommendation.onrender.com"
    ],  # Frontend origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 5. Include the auth, recommendations, and saved books routers with appropriate prefixes
app.include_router(auth_router, prefix="/auth")
app.include_router(recommendations_router, prefix="/recommendations")
app.include_router(books_router)
app.include_router(saved_books_router)


# 6. Create a simple root GET endpoint at "/" that returns a welcome message
@app.get("/")
async def root():
    """
    Root endpoint with welcome message
    """
    return {
        "message": "Welcome to the AI Book Recommendations API!",
        "description": "Get personalized book recommendations using AI",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "auth": "/auth",
            "recommendations": "/recommendations"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Book Recommendations API",
        "version": "1.0.0"
    }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Endpoint not found",
            "message": "The requested endpoint does not exist. Check the API documentation at /docs"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )