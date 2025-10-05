#!/usr/bin/env python3
"""
Development server runner for the Book Recommendations API
Complete functional backend server
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the FastAPI server"""
    print("🚀 Starting Book Recommendations API Server...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔄 Alternative Documentation at: http://localhost:8000/redoc")
    print("=" * 60)
    
    # Run the development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()