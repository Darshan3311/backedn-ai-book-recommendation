#!/usr/bin/env python3
"""
Test server runner - runs without MongoDB for testing API structure
"""

import uvicorn

def main():
    """Run the test FastAPI server without database"""
    print("🧪 Starting Book Recommendations API in TEST MODE...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("⚠️  Note: Database features disabled - for testing API structure only")
    print("=" * 60)
    
    # Run the test server
    uvicorn.run(
        "app.main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()