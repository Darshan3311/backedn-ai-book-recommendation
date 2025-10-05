# Create an in-memory version for testing without MongoDB
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import auth_router, recommendations_router

# Simple startup without database for testing
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - simplified for testing
    """
    print("🚀 Starting Book Recommendations API (Test Mode - No Database)...")
    print("⚠️  Note: This is running without MongoDB - authentication won't work")
    print("✅ You can test the OpenAI recommendations endpoint structure")
    print("🎉 Book Recommendations API is ready!")
    yield
    print("👋 Shutting down Book Recommendations API...")

# Create FastAPI app instance
app = FastAPI(
    title="AI Book Recommendations API (Test Mode)",
    description="Get personalized book recommendations using AI - Test Mode",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (auth won't work without DB, but structure is there)
app.include_router(auth_router, prefix="/auth")
app.include_router(recommendations_router, prefix="/recommendations")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with welcome message"""
    return {
        "message": "Welcome to the AI Book Recommendations API! (Test Mode)",
        "description": "Get personalized book recommendations using AI",
        "version": "1.0.0",
        "status": "Running in test mode - Configure MongoDB to enable full functionality",
        "endpoints": {
            "docs": "/docs",
            "auth": "/auth (requires MongoDB)",
            "recommendations": "/recommendations (requires MongoDB & OpenAI)"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Book Recommendations API",
        "version": "1.0.0",
        "mode": "test"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )